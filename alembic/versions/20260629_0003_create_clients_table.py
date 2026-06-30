"""create clients table

Revision ID: 20260629_0003
Revises: 20260629_0002
Create Date: 2026-06-29 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260629_0003"
down_revision: Union[str, None] = "20260629_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    balance_type = postgresql.ENUM("debit", "credit", name="balance_type", create_type=False)
    create_balance_type = postgresql.ENUM("debit", "credit", name="balance_type")
    create_balance_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("billing_name", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("gstin", sa.String(length=15), nullable=True),
        sa.Column("mobile", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("opening_balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("balance_type", balance_type, nullable=False),
        sa.Column("current_balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clients_client_name"), "clients", ["client_name"], unique=False)
    op.create_index(op.f("ix_clients_gstin"), "clients", ["gstin"], unique=True)
    op.create_index(op.f("ix_clients_id"), "clients", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clients_id"), table_name="clients")
    op.drop_index(op.f("ix_clients_gstin"), table_name="clients")
    op.drop_index(op.f("ix_clients_client_name"), table_name="clients")
    op.drop_table("clients")
    sa.Enum(name="balance_type").drop(op.get_bind(), checkfirst=True)
