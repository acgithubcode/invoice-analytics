from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.bank_statement import BankStatementStatus


class BankStatementCreate(BaseModel):
    transaction_date: date
    description: str | None = None
    reference_no: str | None = Field(default=None, max_length=100)
    debit: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    credit: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    balance: Decimal = Field(max_digits=12, decimal_places=2)

    @model_validator(mode="after")
    def validate_debit_or_credit(self) -> "BankStatementCreate":
        if self.debit == 0 and self.credit == 0:
            raise ValueError("Either debit or credit is required.")
        if self.debit > 0 and self.credit > 0:
            raise ValueError("Only one of debit or credit is allowed.")
        return self


class BankStatementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_date: date
    description: str | None
    reference_no: str | None
    debit: Decimal
    credit: Decimal
    balance: Decimal
    matched_client_id: int | None
    matched_ledger_entry_id: int | None
    status: BankStatementStatus
    created_by_user_id: int
    created_at: datetime


class BankStatementMatchClient(BaseModel):
    client_id: int


class BankStatementImportResult(BaseModel):
    imported: int
    skipped_duplicates: int
    errors: list[str]
