"""add telegram_chat_id to tracked_emails

Revision ID: f921a8d42391
Revises: 8669381141a6
Create Date: 2026-08-15 08:45:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f921a8d42391"
down_revision: Union[str, None] = "8669381141a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("tracked_emails", schema=None) as batch_op:
        batch_op.add_column(sa.Column("telegram_chat_id", sa.String(length=64), nullable=True))
        batch_op.create_index("ix_tracked_emails_telegram_chat_id", ["telegram_chat_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("tracked_emails", schema=None) as batch_op:
        batch_op.drop_index("ix_tracked_emails_telegram_chat_id")
        batch_op.drop_column("telegram_chat_id")
