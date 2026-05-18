"""add user table

Revision ID: 20260227_0001
Revises:
Create Date: 2026-02-27 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260227_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_account", sa.String(length=128), nullable=False),
        sa.Column("user_password", sa.String(length=255), nullable=False),
        sa.Column("user_name", sa.String(length=128), nullable=True),
        sa.Column("user_avatar", sa.String(length=512), nullable=True),
        sa.Column("user_profile", sa.String(length=1024), nullable=True),
        sa.Column("user_role", sa.String(length=32), server_default="user", nullable=False),
        sa.Column("edit_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("update_time", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("is_delete", sa.SmallInteger(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user")),
    )
    op.create_index(op.f("ix_user_user_account"), "user", ["user_account"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_user_account"), table_name="user")
    op.drop_table("user")
