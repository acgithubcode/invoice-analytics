"""create purchase invoices

Revision ID: 20260630_0007
Revises: 20260630_0006
Create Date: 2026-06-30 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260630_0007"
down_revision: Union[str, None] = "20260630_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    purchase_invoice_status = postgresql.ENUM(
        "draft",
        "generated",
        "approved",
        "cancelled",
        name="purchase_invoice_status",
        create_type=False,
    )
    create_purchase_invoice_status = postgresql.ENUM(
        "draft",
        "generated",
        "approved",
        "cancelled",
        name="purchase_invoice_status",
    )
    create_purchase_invoice_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "purchase_invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_invoice_no", sa.String(length=64), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("supplier_name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("gstin", sa.String(length=15), nullable=True),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("igst_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("cgst_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("sgst_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", purchase_invoice_status, nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_purchase_invoices_id"), "purchase_invoices", ["id"], unique=False)
    op.create_index(
        op.f("ix_purchase_invoices_purchase_invoice_no"),
        "purchase_invoices",
        ["purchase_invoice_no"],
        unique=True,
    )

    op.create_table(
        "purchase_invoice_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_invoice_id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["purchase_invoice_id"], ["purchase_invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_purchase_invoice_items_id"), "purchase_invoice_items", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_purchase_invoice_items_id"), table_name="purchase_invoice_items")
    op.drop_table("purchase_invoice_items")
    op.drop_index(op.f("ix_purchase_invoices_purchase_invoice_no"), table_name="purchase_invoices")
    op.drop_index(op.f("ix_purchase_invoices_id"), table_name="purchase_invoices")
    op.drop_table("purchase_invoices")
    sa.Enum(name="purchase_invoice_status").drop(op.get_bind(), checkfirst=True)
