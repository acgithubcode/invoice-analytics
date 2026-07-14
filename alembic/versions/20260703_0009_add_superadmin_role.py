"""add superadmin role

Revision ID: 20260703_0009
Revises: 20260630_0008
Create Date: 2026-07-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260703_0009"
down_revision: Union[str, None] = "20260630_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'superadmin'")


def downgrade() -> None:
    bind = op.get_bind()
    op.execute("UPDATE users SET role = 'admin' WHERE role = 'superadmin'")

    old_role = postgresql.ENUM("employee", "manager", "admin", name="user_role_old")
    old_role.create(bind, checkfirst=True)

    op.alter_column(
        "users",
        "role",
        type_=old_role,
        postgresql_using="role::text::user_role_old",
        existing_nullable=False,
    )
    sa.Enum(name="user_role").drop(bind, checkfirst=True)
    op.execute("ALTER TYPE user_role_old RENAME TO user_role")
