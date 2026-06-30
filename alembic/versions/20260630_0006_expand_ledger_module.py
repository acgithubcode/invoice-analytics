"""expand ledger module

Revision ID: 20260630_0006
Revises: 20260630_0005
Create Date: 2026-06-30 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260630_0006"
down_revision: Union[str, None] = "20260630_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("can_add_manual_ledger_entries", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.alter_column("users", "can_add_manual_ledger_entries", server_default=None)

    op.drop_index(op.f("ix_ledger_entries_id"), table_name="ledger_entries")
    op.drop_table("ledger_entries")
    sa.Enum(name="ledger_entry_type").drop(op.get_bind(), checkfirst=True)

    ledger_entry_type = postgresql.ENUM(
        "sales_invoice",
        "purchase_invoice",
        "payment_received",
        "payment_paid",
        "bank_statement",
        "opening_balance",
        "adjustment",
        name="ledger_entry_type",
        create_type=False,
    )
    create_ledger_entry_type = postgresql.ENUM(
        "sales_invoice",
        "purchase_invoice",
        "payment_received",
        "payment_paid",
        "bank_statement",
        "opening_balance",
        "adjustment",
        name="ledger_entry_type",
    )
    create_ledger_entry_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("entry_type", ledger_entry_type, nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("reference_no", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("debit", sa.Numeric(12, 2), nullable=False),
        sa.Column("credit", sa.Numeric(12, 2), nullable=False),
        sa.Column("balance_after_entry", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entry_type", "reference_id", name="uq_ledger_entries_reference"),
    )
    op.create_index(op.f("ix_ledger_entries_id"), "ledger_entries", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ledger_entries_id"), table_name="ledger_entries")
    op.drop_table("ledger_entries")
    sa.Enum(name="ledger_entry_type").drop(op.get_bind(), checkfirst=True)

    old_ledger_entry_type = postgresql.ENUM("debit", "credit", name="ledger_entry_type", create_type=False)
    create_old_ledger_entry_type = postgresql.ENUM("debit", "credit", name="ledger_entry_type")
    create_old_ledger_entry_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("entry_type", old_ledger_entry_type, nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_type", "source_id", name="uq_ledger_entries_source"),
    )
    op.create_index(op.f("ix_ledger_entries_id"), "ledger_entries", ["id"], unique=False)
    op.drop_column("users", "can_add_manual_ledger_entries")
