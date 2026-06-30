from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.client import Client
from app.models.sales_invoice import SalesInvoice, SalesInvoiceItem, SalesInvoiceStatus
from app.models.user import User
from app.schemas.sales_invoice import SalesInvoiceCreate, SalesInvoiceItemCreate, SalesInvoiceUpdate
from app.services.ledger_service import create_sales_invoice_ledger_entry

MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _normalize_gstin(gstin: str | None) -> str | None:
    if gstin is None:
        return None
    normalized = gstin.strip().upper()
    return normalized or None


def _build_item(payload: SalesInvoiceItemCreate) -> SalesInvoiceItem:
    price = _money(payload.quantity * payload.rate)
    gst_amount = _money(price * payload.gst_rate / Decimal("100"))
    cgst_amount = _money(gst_amount / Decimal("2"))
    sgst_amount = _money(gst_amount - cgst_amount)
    igst_amount = Decimal("0.00")

    return SalesInvoiceItem(
        product_name=payload.product_name,
        hsn_code=payload.hsn_code.strip().upper() if payload.hsn_code else None,
        quantity=payload.quantity,
        rate=payload.rate,
        price=price,
        gst_rate=payload.gst_rate,
        igst_amount=igst_amount,
        cgst_amount=cgst_amount,
        sgst_amount=sgst_amount,
        total_price=_money(price + igst_amount + cgst_amount + sgst_amount),
    )


def _recalculate_totals(invoice: SalesInvoice) -> None:
    invoice.subtotal = _money(sum((item.price for item in invoice.items), Decimal("0.00")))
    invoice.igst_amount = _money(sum((item.igst_amount for item in invoice.items), Decimal("0.00")))
    invoice.cgst_amount = _money(sum((item.cgst_amount for item in invoice.items), Decimal("0.00")))
    invoice.sgst_amount = _money(sum((item.sgst_amount for item in invoice.items), Decimal("0.00")))
    invoice.total_amount = _money(invoice.subtotal + invoice.igst_amount + invoice.cgst_amount + invoice.sgst_amount)


def get_sales_invoice_by_id(db: Session, invoice_id: int) -> SalesInvoice | None:
    statement = (
        select(SalesInvoice)
        .options(selectinload(SalesInvoice.items))
        .where(SalesInvoice.id == invoice_id)
    )
    return db.scalar(statement)


def get_sales_invoice_by_no(db: Session, invoice_no: str) -> SalesInvoice | None:
    return db.scalar(select(SalesInvoice).where(SalesInvoice.invoice_no == invoice_no.strip()))


def list_sales_invoices(db: Session) -> list[SalesInvoice]:
    statement = (
        select(SalesInvoice)
        .options(selectinload(SalesInvoice.items))
        .order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.id.desc())
    )
    return list(db.scalars(statement).all())


def create_sales_invoice(db: Session, payload: SalesInvoiceCreate, current_user: User) -> SalesInvoice:
    client = db.get(Client, payload.client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    if get_sales_invoice_by_no(db, payload.invoice_no):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice number already exists.")

    invoice = SalesInvoice(
        invoice_no=payload.invoice_no.strip(),
        invoice_date=payload.invoice_date,
        vehicle_number=payload.vehicle_number,
        client_id=payload.client_id,
        invoice_to=payload.invoice_to or client.billing_name or client.client_name,
        address=payload.address if payload.address is not None else client.address,
        gstin=_normalize_gstin(payload.gstin if payload.gstin is not None else client.gstin),
        subtotal=Decimal("0.00"),
        igst_amount=Decimal("0.00"),
        cgst_amount=Decimal("0.00"),
        sgst_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
        status=SalesInvoiceStatus.draft,
        created_by_user_id=current_user.id,
        items=[_build_item(item) for item in payload.items],
    )
    _recalculate_totals(invoice)

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return get_sales_invoice_by_id(db, invoice.id) or invoice


def update_sales_invoice(db: Session, invoice: SalesInvoice, payload: SalesInvoiceUpdate) -> SalesInvoice:
    if invoice.status in {
        SalesInvoiceStatus.generated,
        SalesInvoiceStatus.approved,
        SalesInvoiceStatus.cancelled,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Generated, approved, or cancelled invoices cannot be updated.",
        )

    update_data = payload.model_dump(exclude_unset=True, exclude={"items"})
    if "invoice_no" in update_data and update_data["invoice_no"] is not None:
        existing_invoice = get_sales_invoice_by_no(db, update_data["invoice_no"])
        if existing_invoice and existing_invoice.id != invoice.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice number already exists.")
        update_data["invoice_no"] = update_data["invoice_no"].strip()

    if "client_id" in update_data and update_data["client_id"] is not None:
        client = db.get(Client, update_data["client_id"])
        if client is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    if "gstin" in update_data:
        update_data["gstin"] = _normalize_gstin(update_data["gstin"])

    for field, value in update_data.items():
        setattr(invoice, field, value)

    if payload.items is not None:
        invoice.items.clear()
        invoice.items.extend(_build_item(item) for item in payload.items)

    _recalculate_totals(invoice)
    db.commit()
    db.refresh(invoice)
    return get_sales_invoice_by_id(db, invoice.id) or invoice


def generate_sales_invoice(db: Session, invoice: SalesInvoice, current_user: User) -> SalesInvoice:
    if invoice.status == SalesInvoiceStatus.cancelled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cancelled invoice cannot be generated.")
    if invoice.status == SalesInvoiceStatus.draft:
        invoice.status = SalesInvoiceStatus.generated
    create_sales_invoice_ledger_entry(
        db,
        client_id=invoice.client_id,
        invoice_id=invoice.id,
        invoice_no=invoice.invoice_no,
        invoice_date=invoice.invoice_date,
        total_amount=invoice.total_amount,
        current_user=current_user,
    )
    db.commit()
    db.refresh(invoice)
    return get_sales_invoice_by_id(db, invoice.id) or invoice


def approve_sales_invoice(db: Session, invoice: SalesInvoice, current_user: User) -> SalesInvoice:
    if invoice.status == SalesInvoiceStatus.cancelled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cancelled invoice cannot be approved.")
    invoice.status = SalesInvoiceStatus.approved
    invoice.approved_by_user_id = current_user.id
    create_sales_invoice_ledger_entry(
        db,
        client_id=invoice.client_id,
        invoice_id=invoice.id,
        invoice_no=invoice.invoice_no,
        invoice_date=invoice.invoice_date,
        total_amount=invoice.total_amount,
        current_user=current_user,
    )
    db.commit()
    db.refresh(invoice)
    return get_sales_invoice_by_id(db, invoice.id) or invoice


def cancel_sales_invoice(db: Session, invoice: SalesInvoice) -> SalesInvoice:
    if invoice.status == SalesInvoiceStatus.approved:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approved invoice cannot be cancelled.")
    invoice.status = SalesInvoiceStatus.cancelled
    db.commit()
    db.refresh(invoice)
    return get_sales_invoice_by_id(db, invoice.id) or invoice
