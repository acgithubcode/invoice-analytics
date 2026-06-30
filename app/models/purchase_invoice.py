import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PurchaseInvoiceStatus(str, enum.Enum):
    draft = "draft"
    generated = "generated"
    approved = "approved"
    cancelled = "cancelled"


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_invoice_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    igst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PurchaseInvoiceStatus] = mapped_column(
        Enum(PurchaseInvoiceStatus, name="purchase_invoice_status"),
        default=PurchaseInvoiceStatus.draft,
        nullable=False,
    )
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    supplier = relationship("Client")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    items = relationship(
        "PurchaseInvoiceItem",
        back_populates="purchase_invoice",
        cascade="all, delete-orphan",
        order_by="PurchaseInvoiceItem.id",
    )


class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_invoice_id: Mapped[int] = mapped_column(ForeignKey("purchase_invoices.id", ondelete="CASCADE"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hsn_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    igst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    purchase_invoice = relationship("PurchaseInvoice", back_populates="items")
