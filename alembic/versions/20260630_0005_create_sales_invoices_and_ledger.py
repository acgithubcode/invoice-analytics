"""create sales invoices and ledger entries

Revision ID: 20260630_0005
Revises: 20260629_0004
Create Date: 2026-06-30 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260630_0005"
down_revision: Union[str, None] = "20260629_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sales_invoice_status = postgresql.ENUM(
        "draft",
        "generated",
        "approved",
        "cancelled",
        name="sales_invoice_status",
        create_type=False,
    )
    create_sales_invoice_status = postgresql.ENUM(
        "draft",
        "generated",
        "approved",
        "cancelled",
        name="sales_invoice_status",
    )
    create_sales_invoice_status.create(op.get_bind(), checkfirst=True)

    ledger_entry_type = postgresql.ENUM("debit", "credit", name="ledger_entry_type", create_type=False)
    create_ledger_entry_type = postgresql.ENUM("debit", "credit", name="ledger_entry_type")
    create_ledger_entry_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "sales_invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_no", sa.String(length=64), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("vehicle_number", sa.String(length=50), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("invoice_to", sa.String(length=255), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("gstin", sa.String(length=15), nullable=True),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("igst_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("cgst_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("sgst_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sales_invoice_status, nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sales_invoices_id"), "sales_invoices", ["id"], unique=False)
    op.create_index(op.f("ix_sales_invoices_invoice_no"), "sales_invoices", ["invoice_no"], unique=True)

    op.create_table(
        "sales_invoice_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("hsn_code", sa.String(length=32), nullable=True),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("gst_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("igst_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("cgst_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("sgst_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["sales_invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sales_invoice_items_id"), "sales_invoice_items", ["id"], unique=False)

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("entry_type", ledger_entry_type, nullable=False),
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


def downgrade() -> None:
    op.drop_index(op.f("ix_ledger_entries_id"), table_name="ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_index(op.f("ix_sales_invoice_items_id"), table_name="sales_invoice_items")
    op.drop_table("sales_invoice_items")
    op.drop_index(op.f("ix_sales_invoices_invoice_no"), table_name="sales_invoices")
    op.drop_index(op.f("ix_sales_invoices_id"), table_name="sales_invoices")
    op.drop_table("sales_invoices")
    sa.Enum(name="ledger_entry_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sales_invoice_status").drop(op.get_bind(), checkfirst=True)
