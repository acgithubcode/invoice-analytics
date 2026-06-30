from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user, manager_or_admin
from app.models.purchase_invoice import PurchaseInvoice
from app.models.user import User
from app.schemas.purchase_invoice import PurchaseInvoiceCreate, PurchaseInvoiceRead, PurchaseInvoiceUpdate
from app.services.purchase_invoice_service import (
    approve_purchase_invoice,
    cancel_purchase_invoice,
    create_purchase_invoice,
    generate_purchase_invoice,
    get_purchase_invoice_by_id,
    list_purchase_invoices,
    update_purchase_invoice,
)

router = APIRouter()


@router.post("", response_model=PurchaseInvoiceRead, status_code=status.HTTP_201_CREATED)
def create_new_purchase_invoice(
    payload: PurchaseInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> PurchaseInvoice:
    return create_purchase_invoice(db, payload, current_user)


@router.get("", response_model=list[PurchaseInvoiceRead])
def read_purchase_invoices(
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> list[PurchaseInvoice]:
    return list_purchase_invoices(db)


@router.get("/{purchase_invoice_id}", response_model=PurchaseInvoiceRead)
def read_purchase_invoice(
    purchase_invoice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> PurchaseInvoice:
    invoice = get_purchase_invoice_by_id(db, purchase_invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found.")
    return invoice


@router.put("/{purchase_invoice_id}", response_model=PurchaseInvoiceRead)
def update_existing_purchase_invoice(
    purchase_invoice_id: int,
    payload: PurchaseInvoiceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> PurchaseInvoice:
    invoice = get_purchase_invoice_by_id(db, purchase_invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found.")
    return update_purchase_invoice(db, invoice, payload)


@router.post("/{purchase_invoice_id}/generate", response_model=PurchaseInvoiceRead)
def generate_existing_purchase_invoice(
    purchase_invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> PurchaseInvoice:
    invoice = get_purchase_invoice_by_id(db, purchase_invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found.")
    return generate_purchase_invoice(db, invoice, current_user)


@router.post("/{purchase_invoice_id}/approve", response_model=PurchaseInvoiceRead, dependencies=[Depends(manager_or_admin)])
def approve_existing_purchase_invoice(
    purchase_invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> PurchaseInvoice:
    invoice = get_purchase_invoice_by_id(db, purchase_invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found.")
    return approve_purchase_invoice(db, invoice, current_user)


@router.post("/{purchase_invoice_id}/cancel", response_model=PurchaseInvoiceRead)
def cancel_existing_purchase_invoice(
    purchase_invoice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> PurchaseInvoice:
    invoice = get_purchase_invoice_by_id(db, purchase_invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found.")
    return cancel_purchase_invoice(db, invoice)
