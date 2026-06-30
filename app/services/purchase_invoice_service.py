from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.client import Client
from app.models.purchase_invoice import PurchaseInvoice, PurchaseInvoiceItem, PurchaseInvoiceStatus
from app.models.user import User
from app.schemas.purchase_invoice import PurchaseInvoiceCreate, PurchaseInvoiceItemCreate, PurchaseInvoiceUpdate
from app.services.ledger_service import create_purchase_invoice_ledger_entry

MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _normalize_gstin(gstin: str | None) -> str | None:
    if gstin is None:
        return None
    normalized = gstin.strip().upper()
    return normalized or None


def _build_item(payload: PurchaseInvoiceItemCreate) -> PurchaseInvoiceItem:
    price = _money(payload.quantity * payload.rate)
    gst_amount = _money(price * payload.gst_rate / Decimal("100"))
    cgst_amount = _money(gst_amount / Decimal("2"))
    sgst_amount = _money(gst_amount - cgst_amount)
    igst_amount = Decimal("0.00")

    return PurchaseInvoiceItem(
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


def _recalculate_totals(invoice: PurchaseInvoice) -> None:
    invoice.subtotal = _money(sum((item.price for item in invoice.items), Decimal("0.00")))
    invoice.igst_amount = _money(sum((item.igst_amount for item in invoice.items), Decimal("0.00")))
    invoice.cgst_amount = _money(sum((item.cgst_amount for item in invoice.items), Decimal("0.00")))
    invoice.sgst_amount = _money(sum((item.sgst_amount for item in invoice.items), Decimal("0.00")))
    invoice.total_amount = _money(invoice.subtotal + invoice.igst_amount + invoice.cgst_amount + invoice.sgst_amount)


def get_purchase_invoice_by_id(db: Session, purchase_invoice_id: int) -> PurchaseInvoice | None:
    statement = (
        select(PurchaseInvoice)
        .options(selectinload(PurchaseInvoice.items))
        .where(PurchaseInvoice.id == purchase_invoice_id)
    )
    return db.scalar(statement)


def get_purchase_invoice_by_no(db: Session, purchase_invoice_no: str) -> PurchaseInvoice | None:
    return db.scalar(select(PurchaseInvoice).where(PurchaseInvoice.purchase_invoice_no == purchase_invoice_no.strip()))


def list_purchase_invoices(db: Session) -> list[PurchaseInvoice]:
    statement = (
        select(PurchaseInvoice)
        .options(selectinload(PurchaseInvoice.items))
        .order_by(PurchaseInvoice.purchase_date.desc(), PurchaseInvoice.id.desc())
    )
    return list(db.scalars(statement).all())


def create_purchase_invoice(db: Session, payload: PurchaseInvoiceCreate, current_user: User) -> PurchaseInvoice:
    supplier = db.get(Client, payload.supplier_id)
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found.")
    if get_purchase_invoice_by_no(db, payload.purchase_invoice_no):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Purchase invoice number already exists.")

    invoice = PurchaseInvoice(
        purchase_invoice_no=payload.purchase_invoice_no.strip(),
        purchase_date=payload.purchase_date,
        supplier_id=payload.supplier_id,
        supplier_name=payload.supplier_name or supplier.billing_name or supplier.client_name,
        address=payload.address if payload.address is not None else supplier.address,
        gstin=_normalize_gstin(payload.gstin if payload.gstin is not None else supplier.gstin),
        subtotal=Decimal("0.00"),
        igst_amount=Decimal("0.00"),
        cgst_amount=Decimal("0.00"),
        sgst_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
        status=PurchaseInvoiceStatus.draft,
        created_by_user_id=current_user.id,
        items=[_build_item(item) for item in payload.items],
    )
    _recalculate_totals(invoice)

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return get_purchase_invoice_by_id(db, invoice.id) or invoice


def update_purchase_invoice(db: Session, invoice: PurchaseInvoice, payload: PurchaseInvoiceUpdate) -> PurchaseInvoice:
    if invoice.status in {
        PurchaseInvoiceStatus.generated,
        PurchaseInvoiceStatus.approved,
        PurchaseInvoiceStatus.cancelled,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Generated, approved, or cancelled purchase invoices cannot be updated.",
        )

    update_data = payload.model_dump(exclude_unset=True, exclude={"items"})
    if "purchase_invoice_no" in update_data and update_data["purchase_invoice_no"] is not None:
        existing_invoice = get_purchase_invoice_by_no(db, update_data["purchase_invoice_no"])
        if existing_invoice and existing_invoice.id != invoice.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Purchase invoice number already exists.")
        update_data["purchase_invoice_no"] = update_data["purchase_invoice_no"].strip()

    if "supplier_id" in update_data and update_data["supplier_id"] is not None:
        supplier = db.get(Client, update_data["supplier_id"])
        if supplier is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found.")

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
    return get_purchase_invoice_by_id(db, invoice.id) or invoice


def generate_purchase_invoice(db: Session, invoice: PurchaseInvoice, current_user: User) -> PurchaseInvoice:
    if invoice.status == PurchaseInvoiceStatus.cancelled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cancelled purchase invoice cannot be generated.")
    if invoice.status == PurchaseInvoiceStatus.draft:
        invoice.status = PurchaseInvoiceStatus.generated
    create_purchase_invoice_ledger_entry(
        db,
        supplier_id=invoice.supplier_id,
        purchase_invoice_id=invoice.id,
        purchase_invoice_no=invoice.purchase_invoice_no,
        purchase_date=invoice.purchase_date,
        total_amount=invoice.total_amount,
        current_user=current_user,
    )
    db.commit()
    db.refresh(invoice)
    return get_purchase_invoice_by_id(db, invoice.id) or invoice


def approve_purchase_invoice(db: Session, invoice: PurchaseInvoice, current_user: User) -> PurchaseInvoice:
    if invoice.status == PurchaseInvoiceStatus.cancelled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cancelled purchase invoice cannot be approved.")
    invoice.status = PurchaseInvoiceStatus.approved
    invoice.approved_by_user_id = current_user.id
    create_purchase_invoice_ledger_entry(
        db,
        supplier_id=invoice.supplier_id,
        purchase_invoice_id=invoice.id,
        purchase_invoice_no=invoice.purchase_invoice_no,
        purchase_date=invoice.purchase_date,
        total_amount=invoice.total_amount,
        current_user=current_user,
    )
    db.commit()
    db.refresh(invoice)
    return get_purchase_invoice_by_id(db, invoice.id) or invoice


def cancel_purchase_invoice(db: Session, invoice: PurchaseInvoice) -> PurchaseInvoice:
    if invoice.status == PurchaseInvoiceStatus.approved:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approved purchase invoice cannot be cancelled.")
    invoice.status = PurchaseInvoiceStatus.cancelled
    db.commit()
    db.refresh(invoice)
    return get_purchase_invoice_by_id(db, invoice.id) or invoice
