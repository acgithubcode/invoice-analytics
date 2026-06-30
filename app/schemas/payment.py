from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMode, PaymentType


class PaymentCreate(BaseModel):
    client_id: int
    payment_date: date
    payment_type: PaymentType
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payment_mode: PaymentMode
    bank_name: str | None = Field(default=None, max_length=255)
    transaction_no: str | None = Field(default=None, max_length=100)
    remarks: str | None = None


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    payment_date: date
    payment_type: PaymentType
    amount: Decimal
    payment_mode: PaymentMode
    bank_name: str | None
    transaction_no: str | None
    remarks: str | None
    created_by_user_id: int
    created_at: datetime
