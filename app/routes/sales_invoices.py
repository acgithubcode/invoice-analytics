from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user, manager_or_admin
from app.models.sales_invoice import SalesInvoice
from app.models.user import User
from app.schemas.sales_invoice import SalesInvoiceCreate, SalesInvoiceRead, SalesInvoiceUpdate
from app.services.sales_invoice_service import (
    approve_sales_invoice,
    cancel_sales_invoice,
    create_sales_invoice,
    generate_sales_invoice,
    get_sales_invoice_by_id,
    list_sales_invoices,
    update_sales_invoice,
)

router = APIRouter()


@router.post("", response_model=SalesInvoiceRead, status_code=status.HTTP_201_CREATED)
def create_new_sales_invoice(
    payload: SalesInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> SalesInvoice:
    return create_sales_invoice(db, payload, current_user)


@router.get("", response_model=list[SalesInvoiceRead])
def read_sales_invoices(
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> list[SalesInvoice]:
    return list_sales_invoices(db)


@router.get("/{invoice_id}", response_model=SalesInvoiceRead)
def read_sales_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> SalesInvoice:
    invoice = get_sales_invoice_by_id(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales invoice not found.")
    return invoice


@router.put("/{invoice_id}", response_model=SalesInvoiceRead)
def update_existing_sales_invoice(
    invoice_id: int,
    payload: SalesInvoiceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> SalesInvoice:
    invoice = get_sales_invoice_by_id(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales invoice not found.")
    return update_sales_invoice(db, invoice, payload)


@router.post("/{invoice_id}/generate", response_model=SalesInvoiceRead)
def generate_existing_sales_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> SalesInvoice:
    invoice = get_sales_invoice_by_id(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales invoice not found.")
    return generate_sales_invoice(db, invoice, current_user)


@router.post("/{invoice_id}/approve", response_model=SalesInvoiceRead, dependencies=[Depends(manager_or_admin)])
def approve_existing_sales_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> SalesInvoice:
    invoice = get_sales_invoice_by_id(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales invoice not found.")
    return approve_sales_invoice(db, invoice, current_user)


@router.post("/{invoice_id}/cancel", response_model=SalesInvoiceRead)
def cancel_existing_sales_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> SalesInvoice:
    invoice = get_sales_invoice_by_id(db, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales invoice not found.")
    return cancel_sales_invoice(db, invoice)
