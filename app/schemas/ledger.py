from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.ledger import LedgerEntryType


class LedgerEntryCreate(BaseModel):
    client_id: int
    entry_date: date
    entry_type: LedgerEntryType
    reference_id: int | None = None
    reference_no: str | None = Field(default=None, max_length=100)
    description: str | None = None
    debit: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    credit: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)

    @model_validator(mode="after")
    def validate_debit_or_credit(self) -> "LedgerEntryCreate":
        if self.debit == 0 and self.credit == 0:
            raise ValueError("Either debit or credit is required.")
        if self.debit > 0 and self.credit > 0:
            raise ValueError("Only one of debit or credit is allowed.")
        return self


class LedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    entry_date: date
    entry_type: LedgerEntryType
    reference_id: int | None
    reference_no: str | None
    description: str | None
    debit: Decimal
    credit: Decimal
    balance_after_entry: Decimal
    created_by_user_id: int
    created_at: datetime


class LedgerSummary(BaseModel):
    client_id: int
    opening_balance: Decimal
    total_debit: Decimal
    total_credit: Decimal
    current_balance: Decimal
