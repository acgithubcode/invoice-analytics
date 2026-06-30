from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import Role, User
from app.schemas.invoice import InvoiceCreate


def create_invoice(db: Session, payload: InvoiceCreate, current_user: User) -> Invoice:
    invoice = Invoice(
        invoice_number=payload.invoice_number,
        customer_name=payload.customer_name,
        amount=payload.amount,
        description=payload.description,
        created_by_id=current_user.id,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def get_invoice_by_id(db: Session, invoice_id: int) -> Invoice | None:
    return db.get(Invoice, invoice_id)


def list_invoices(db: Session, current_user: User) -> list[Invoice]:
    statement = select(Invoice).order_by(Invoice.created_at.desc())
    if current_user.role == Role.employee:
        statement = statement.where(Invoice.created_by_id == current_user.id)
    return list(db.scalars(statement).all())


def approve_invoice(db: Session, invoice: Invoice, status: InvoiceStatus, current_user: User) -> Invoice:
    invoice.status = status
    invoice.approved_by_id = current_user.id
    invoice.approved_at = datetime.now(UTC)
    db.commit()
    db.refresh(invoice)
    return invoice
