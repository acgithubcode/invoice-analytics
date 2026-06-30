from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.invoice import InvoiceStatus


class InvoiceCreate(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=64)
    customer_name: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    description: str | None = None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    customer_name: str
    amount: Decimal
    description: str | None
    status: InvoiceStatus
    created_by_id: int
    approved_by_id: int | None
    created_at: datetime
    approved_at: datetime | None


class InvoiceApproval(BaseModel):
    status: Literal[InvoiceStatus.approved, InvoiceStatus.rejected]
