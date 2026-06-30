from datetime import date
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.client import BalanceType, Client
from app.models.ledger import LedgerEntry
from app.models.payment import Payment, PaymentType
from app.models.purchase_invoice import PurchaseInvoice, PurchaseInvoiceStatus
from app.models.sales_invoice import SalesInvoice, SalesInvoiceStatus
from app.models.user import Role, User


POSTED_SALES_STATUSES = (SalesInvoiceStatus.generated, SalesInvoiceStatus.approved)
POSTED_PURCHASE_STATUSES = (PurchaseInvoiceStatus.generated, PurchaseInvoiceStatus.approved)


def _decimal(value) -> Decimal:
    return value if value is not None else Decimal("0.00")


def _is_limited_user(current_user: User) -> bool:
    return current_user.role == Role.employee


def _apply_sales_access(statement: Select, current_user: User) -> Select:
    if _is_limited_user(current_user):
        return statement.where(SalesInvoice.created_by_user_id == current_user.id)
    return statement


def _apply_purchase_access(statement: Select, current_user: User) -> Select:
    if _is_limited_user(current_user):
        return statement.where(PurchaseInvoice.created_by_user_id == current_user.id)
    return statement


def get_dashboard_report(db: Session, current_user: User) -> dict:
    today = date.today()

    sales_statement = select(func.coalesce(func.sum(SalesInvoice.total_amount), 0)).where(
        SalesInvoice.status.in_(POSTED_SALES_STATUSES)
    )
    sales_statement = _apply_sales_access(sales_statement, current_user)

    purchase_statement = select(func.coalesce(func.sum(PurchaseInvoice.total_amount), 0)).where(
        PurchaseInvoice.status.in_(POSTED_PURCHASE_STATUSES)
    )
    purchase_statement = _apply_purchase_access(purchase_statement, current_user)

    pending_sales_statement = select(func.count(SalesInvoice.id)).where(SalesInvoice.status == SalesInvoiceStatus.generated)
    pending_sales_statement = _apply_sales_access(pending_sales_statement, current_user)

    today_collection_statement = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.payment_type == PaymentType.received,
        Payment.payment_date == today,
    )
    if _is_limited_user(current_user):
        today_collection_statement = today_collection_statement.where(Payment.created_by_user_id == current_user.id)

    balances = get_client_balances_report(db)
    total_receivable = sum((row["current_balance"] for row in balances if row["current_balance"] > 0), Decimal("0.00"))
    total_payable = abs(sum((row["current_balance"] for row in balances if row["current_balance"] < 0), Decimal("0.00")))

    return {
        "total_sales": _decimal(db.scalar(sales_statement)),
        "total_purchase": _decimal(db.scalar(purchase_statement)),
        "total_receivable": total_receivable,
        "total_payable": total_payable,
        "total_clients": db.scalar(select(func.count(Client.id))) or 0,
        "pending_invoices": db.scalar(pending_sales_statement) or 0,
        "today_collection": _decimal(db.scalar(today_collection_statement)),
    }


def get_client_balances_report(db: Session) -> list[dict]:
    clients = list(db.scalars(select(Client).order_by(Client.client_name.asc())).all())
    rows: list[dict] = []
    for client in clients:
        entries = list(db.scalars(select(LedgerEntry).where(LedgerEntry.client_id == client.id)).all())
        opening_balance = client.opening_balance if client.balance_type == BalanceType.debit else -client.opening_balance
        total_debit = sum((entry.debit for entry in entries), Decimal("0.00"))
        total_credit = sum((entry.credit for entry in entries), Decimal("0.00"))
        current_balance = opening_balance + total_debit - total_credit
        rows.append(
            {
                "client_id": client.id,
                "client_name": client.client_name,
                "total_debit": total_debit,
                "total_credit": total_credit,
                "current_balance": current_balance,
                "balance_type": "receivable" if current_balance >= 0 else "payable",
            }
        )
    return rows


def get_sales_register(
    db: Session,
    current_user: User,
    from_date: date | None = None,
    to_date: date | None = None,
    client_id: int | None = None,
) -> list[SalesInvoice]:
    statement = select(SalesInvoice).order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.id.desc())
    statement = _apply_sales_access(statement, current_user)
    if from_date:
        statement = statement.where(SalesInvoice.invoice_date >= from_date)
    if to_date:
        statement = statement.where(SalesInvoice.invoice_date <= to_date)
    if client_id:
        statement = statement.where(SalesInvoice.client_id == client_id)
    return list(db.scalars(statement).all())


def get_purchase_register(
    db: Session,
    current_user: User,
    from_date: date | None = None,
    to_date: date | None = None,
    supplier_id: int | None = None,
) -> list[PurchaseInvoice]:
    statement = select(PurchaseInvoice).order_by(PurchaseInvoice.purchase_date.desc(), PurchaseInvoice.id.desc())
    statement = _apply_purchase_access(statement, current_user)
    if from_date:
        statement = statement.where(PurchaseInvoice.purchase_date >= from_date)
    if to_date:
        statement = statement.where(PurchaseInvoice.purchase_date <= to_date)
    if supplier_id:
        statement = statement.where(PurchaseInvoice.supplier_id == supplier_id)
    return list(db.scalars(statement).all())


def get_gst_summary(
    db: Session,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    sales_statement = select(
        func.coalesce(func.sum(SalesInvoice.subtotal), 0),
        func.coalesce(func.sum(SalesInvoice.igst_amount), 0),
        func.coalesce(func.sum(SalesInvoice.cgst_amount), 0),
        func.coalesce(func.sum(SalesInvoice.sgst_amount), 0),
        func.coalesce(func.sum(SalesInvoice.total_amount), 0),
    ).where(SalesInvoice.status.in_(POSTED_SALES_STATUSES))

    if from_date:
        sales_statement = sales_statement.where(SalesInvoice.invoice_date >= from_date)
    if to_date:
        sales_statement = sales_statement.where(SalesInvoice.invoice_date <= to_date)

    taxable_amount, igst, cgst, sgst, total_invoice_amount = db.execute(sales_statement).one()
    return {
        "taxable_amount": taxable_amount,
        "igst": igst,
        "cgst": cgst,
        "sgst": sgst,
        "total_invoice_amount": total_invoice_amount,
    }
