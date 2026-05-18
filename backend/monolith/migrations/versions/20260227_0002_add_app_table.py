"""add app table

Revision ID: 20260227_0002
Revises: 20260227_0001
Create Date: 2026-02-27 00:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260227_0002"
down_revision: str | None = "20260227_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("app_name", sa.String(length=128), server_default="My App", nullable=False),
        sa.Column("cover", sa.String(length=512), nullable=True),
        sa.Column("init_prompt", sa.Text(), nullable=True),
        sa.Column("code_gen_type", sa.String(length=32), server_default="html", nullable=False),
        sa.Column("deploy_key", sa.String(length=128), nullable=True),
        sa.Column("deployed_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("create_time", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("update_time", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("is_delete", sa.SmallInteger(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_app_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app")),
    )
    op.create_index(op.f("ix_app_user_id"), "app", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_app_user_id"), table_name="app")
    op.drop_table("app")
