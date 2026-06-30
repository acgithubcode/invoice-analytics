import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BankStatementStatus(str, enum.Enum):
    unmatched = "unmatched"
    matched = "matched"


class BankStatement(Base):
    __tablename__ = "bank_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_no: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    debit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    credit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    matched_client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True)
    matched_ledger_entry_id: Mapped[int | None] = mapped_column(ForeignKey("ledger_entries.id"), nullable=True)
    status: Mapped[BankStatementStatus] = mapped_column(
        Enum(BankStatementStatus, name="bank_statement_status"),
        default=BankStatementStatus.unmatched,
        nullable=False,
    )
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    matched_client = relationship("Client")
    matched_ledger_entry = relationship("LedgerEntry")
    created_by = relationship("User")
