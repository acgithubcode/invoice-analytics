from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import PaymentCreate
from app.services.ledger_service import create_payment_ledger_entry
from fastapi import HTTPException, status


def get_payment_by_id(db: Session, payment_id: int) -> Payment | None:
    return db.get(Payment, payment_id)


def get_payment_by_transaction_no(db: Session, transaction_no: str | None) -> Payment | None:
    if not transaction_no:
        return None
    return db.scalar(select(Payment).where(Payment.transaction_no == transaction_no.strip()))


def create_payment(db: Session, payload: PaymentCreate, current_user: User) -> Payment:
    client = db.get(Client, payload.client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    transaction_no = payload.transaction_no.strip() if payload.transaction_no else None
    if get_payment_by_transaction_no(db, transaction_no):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transaction number already exists.")

    payment = Payment(
        client_id=payload.client_id,
        payment_date=payload.payment_date,
        payment_type=payload.payment_type,
        amount=payload.amount,
        payment_mode=payload.payment_mode,
        bank_name=payload.bank_name,
        transaction_no=transaction_no,
        remarks=payload.remarks,
        created_by_user_id=current_user.id,
    )
    db.add(payment)
    db.flush()
    create_payment_ledger_entry(
        db,
        client_id=payment.client_id,
        payment_id=payment.id,
        payment_date=payment.payment_date,
        payment_type=payment.payment_type,
        amount=payment.amount,
        transaction_no=payment.transaction_no,
        current_user=current_user,
    )
    db.commit()
    db.refresh(payment)
    return payment


def list_payments(db: Session) -> list[Payment]:
    return list(db.scalars(select(Payment).order_by(Payment.payment_date.desc(), Payment.id.desc())).all())
