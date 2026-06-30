from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentRead
from app.services.payment_service import create_payment, get_payment_by_id, list_payments

router = APIRouter()


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_new_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> Payment:
    return create_payment(db, payload, current_user)


@router.get("", response_model=list[PaymentRead])
def read_payments(
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> list[Payment]:
    return list_payments(db)


@router.get("/{payment_id}", response_model=PaymentRead)
def read_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> Payment:
    payment = get_payment_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    return payment
