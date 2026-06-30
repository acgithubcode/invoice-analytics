from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user, manager_or_admin
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.invoice import InvoiceApproval, InvoiceCreate, InvoiceRead
from app.services.invoice_service import approve_invoice, create_invoice, get_invoice_by_id, list_invoices

router = APIRouter()


@router.post("", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_new_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> Invoice:
    return create_invoice(db, payload, current_user)


@router.get("", response_model=list[InvoiceRead], dependencies=[Depends(manager_or_admin)])
def read_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> list[Invoice]:
    return list_invoices(db, current_user)


@router.patch("/{invoice_id}/approval", response_model=InvoiceRead, dependencies=[Depends(manager_or_admin)])
def update_invoice_approval(
    invoice_id: int,
    payload: InvoiceApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> Invoice:
    invoice = get_invoice_by_id(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    return approve_invoice(db, invoice, payload.status, current_user)
