"""create payments and bank statements

Revision ID: 20260630_0008
Revises: 20260630_0007
Create Date: 2026-06-30 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260630_0008"
down_revision: Union[str, None] = "20260630_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    payment_type = postgresql.ENUM("received", "paid", name="payment_type", create_type=False)
    create_payment_type = postgresql.ENUM("received", "paid", name="payment_type")
    create_payment_type.create(op.get_bind(), checkfirst=True)

    payment_mode = postgresql.ENUM("cash", "bank", "upi", "cheque", name="payment_mode", create_type=False)
    create_payment_mode = postgresql.ENUM("cash", "bank", "upi", "cheque", name="payment_mode")
    create_payment_mode.create(op.get_bind(), checkfirst=True)

    bank_statement_status = postgresql.ENUM("unmatched", "matched", name="bank_statement_status", create_type=False)
    create_bank_statement_status = postgresql.ENUM("unmatched", "matched", name="bank_statement_status")
    create_bank_statement_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("payment_type", payment_type, nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_mode", payment_mode, nullable=False),
        sa.Column("bank_name", sa.String(length=255), nullable=True),
        sa.Column("transaction_no", sa.String(length=100), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payments_id"), "payments", ["id"], unique=False)
    op.create_index(op.f("ix_payments_transaction_no"), "payments", ["transaction_no"], unique=True)

    op.create_table(
        "bank_statements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference_no", sa.String(length=100), nullable=True),
        sa.Column("debit", sa.Numeric(12, 2), nullable=False),
        sa.Column("credit", sa.Numeric(12, 2), nullable=False),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("matched_client_id", sa.Integer(), nullable=True),
        sa.Column("matched_ledger_entry_id", sa.Integer(), nullable=True),
        sa.Column("status", bank_statement_status, nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["matched_client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["matched_ledger_entry_id"], ["ledger_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bank_statements_id"), "bank_statements", ["id"], unique=False)
    op.create_index(op.f("ix_bank_statements_reference_no"), "bank_statements", ["reference_no"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_bank_statements_reference_no"), table_name="bank_statements")
    op.drop_index(op.f("ix_bank_statements_id"), table_name="bank_statements")
    op.drop_table("bank_statements")
    op.drop_index(op.f("ix_payments_transaction_no"), table_name="payments")
    op.drop_index(op.f("ix_payments_id"), table_name="payments")
    op.drop_table("payments")
    sa.Enum(name="bank_statement_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_mode").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_type").drop(op.get_bind(), checkfirst=True)
