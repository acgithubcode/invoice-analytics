from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    hsn_code: str | None = Field(default=None, max_length=32)
    default_rate: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    gst_rate: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    unit: str = Field(min_length=1, max_length=50)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    hsn_code: str | None = Field(default=None, max_length=32)
    default_rate: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    gst_rate: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    unit: str | None = Field(default=None, min_length=1, max_length=50)
    is_active: bool | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
