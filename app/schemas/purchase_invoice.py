from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.purchase_invoice import PurchaseInvoiceStatus


class PurchaseInvoiceItemBase(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    hsn_code: str | None = Field(default=None, max_length=32)
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    rate: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    gst_rate: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)


class PurchaseInvoiceItemCreate(PurchaseInvoiceItemBase):
    pass


class PurchaseInvoiceItemRead(PurchaseInvoiceItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_invoice_id: int
    price: Decimal
    igst_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    total_price: Decimal


class PurchaseInvoiceBase(BaseModel):
    purchase_invoice_no: str = Field(min_length=1, max_length=64)
    purchase_date: date
    supplier_id: int
    supplier_name: str | None = Field(default=None, max_length=255)
    address: str | None = None
    gstin: str | None = Field(default=None, min_length=15, max_length=15)


class PurchaseInvoiceCreate(PurchaseInvoiceBase):
    items: list[PurchaseInvoiceItemCreate] = Field(min_length=1)


class PurchaseInvoiceUpdate(BaseModel):
    purchase_invoice_no: str | None = Field(default=None, min_length=1, max_length=64)
    purchase_date: date | None = None
    supplier_id: int | None = None
    supplier_name: str | None = Field(default=None, max_length=255)
    address: str | None = None
    gstin: str | None = Field(default=None, min_length=15, max_length=15)
    items: list[PurchaseInvoiceItemCreate] | None = Field(default=None, min_length=1)


class PurchaseInvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_invoice_no: str
    purchase_date: date
    supplier_id: int
    supplier_name: str
    address: str | None
    gstin: str | None
    subtotal: Decimal
    igst_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    total_amount: Decimal
    status: PurchaseInvoiceStatus
    created_by_user_id: int
    approved_by_user_id: int | None
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseInvoiceItemRead]
