from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.client import BalanceType


class ClientBase(BaseModel):
    client_name: str = Field(min_length=1, max_length=255)
    billing_name: str | None = Field(default=None, max_length=255)
    address: str | None = None
    gstin: str | None = Field(default=None, min_length=15, max_length=15)
    mobile: str | None = Field(default=None, min_length=7, max_length=20)
    email: EmailStr | None = None
    opening_balance: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    balance_type: BalanceType = BalanceType.debit
    current_balance: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    client_name: str | None = Field(default=None, min_length=1, max_length=255)
    billing_name: str | None = Field(default=None, max_length=255)
    address: str | None = None
    gstin: str | None = Field(default=None, min_length=15, max_length=15)
    mobile: str | None = Field(default=None, min_length=7, max_length=20)
    email: EmailStr | None = None
    opening_balance: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    balance_type: BalanceType | None = None
    current_balance: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_name: str
    billing_name: str | None
    address: str | None
    gstin: str | None
    mobile: str | None
    email: EmailStr | None
    opening_balance: Decimal
    balance_type: BalanceType
    current_balance: Decimal
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


class ClientImportError(BaseModel):
    row: int
    message: str


class ClientImportResult(BaseModel):
    inserted: int
    updated: int
    skipped_duplicates: int
    skipped_invalid: int
    errors: list[ClientImportError] = []
