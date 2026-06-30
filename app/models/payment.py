import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PaymentType(str, enum.Enum):
    received = "received"
    paid = "paid"


class PaymentMode(str, enum.Enum):
    cash = "cash"
    bank = "bank"
    upi = "upi"
    cheque = "cheque"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType, name="payment_type"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_mode: Mapped[PaymentMode] = mapped_column(Enum(PaymentMode, name="payment_mode"), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transaction_no: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    client = relationship("Client")
    created_by = relationship("User")
