from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.sales_invoice import SalesInvoiceStatus


class SalesInvoiceItemBase(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    hsn_code: str | None = Field(default=None, max_length=32)
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    rate: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    gst_rate: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)


class SalesInvoiceItemCreate(SalesInvoiceItemBase):
    pass


class SalesInvoiceItemRead(SalesInvoiceItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    price: Decimal
    igst_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    total_price: Decimal


class SalesInvoiceBase(BaseModel):
    invoice_no: str = Field(min_length=1, max_length=64)
    invoice_date: date
    vehicle_number: str | None = Field(default=None, max_length=50)
    client_id: int
    invoice_to: str | None = Field(default=None, max_length=255)
    address: str | None = None
    gstin: str | None = Field(default=None, min_length=15, max_length=15)


class SalesInvoiceCreate(SalesInvoiceBase):
    items: list[SalesInvoiceItemCreate] = Field(min_length=1)


class SalesInvoiceUpdate(BaseModel):
    invoice_no: str | None = Field(default=None, min_length=1, max_length=64)
    invoice_date: date | None = None
    vehicle_number: str | None = Field(default=None, max_length=50)
    client_id: int | None = None
    invoice_to: str | None = Field(default=None, max_length=255)
    address: str | None = None
    gstin: str | None = Field(default=None, min_length=15, max_length=15)
    items: list[SalesInvoiceItemCreate] | None = Field(default=None, min_length=1)


class SalesInvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_no: str
    invoice_date: date
    vehicle_number: str | None
    client_id: int
    invoice_to: str
    address: str | None
    gstin: str | None
    subtotal: Decimal
    igst_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    total_amount: Decimal
    status: SalesInvoiceStatus
    created_by_user_id: int
    approved_by_user_id: int | None
    created_at: datetime
    updated_at: datetime
    items: list[SalesInvoiceItemRead]
