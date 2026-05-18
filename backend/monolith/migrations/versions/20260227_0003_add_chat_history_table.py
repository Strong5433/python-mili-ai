"""add chat_history table

Revision ID: 20260227_0003
Revises: 20260227_0002
Create Date: 2026-02-27 15:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260227_0003"
down_revision: str | None = "20260227_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(length=32), nullable=False),
        sa.Column("app_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("create_time", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("update_time", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("is_delete", sa.SmallInteger(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["app_id"], ["app.id"], name=op.f("fk_chat_history_app_id_app")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_chat_history_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_history")),
    )
    op.create_index(op.f("ix_chat_history_app_id"), "chat_history", ["app_id"], unique=False)
    op.create_index(op.f("ix_chat_history_user_id"), "chat_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_chat_history_message_type"), "chat_history", ["message_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_chat_history_message_type"), table_name="chat_history")
    op.drop_index(op.f("ix_chat_history_user_id"), table_name="chat_history")
    op.drop_index(op.f("ix_chat_history_app_id"), table_name="chat_history")
    op.drop_table("chat_history")
