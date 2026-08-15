"""add notify_limit and notify_forwarding to tracked_emails

Revision ID: c57a24e931b2
Revises: f921a8d42391
Create Date: 2026-08-15 12:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "c57a24e931b2"
down_revision: Union[str, None] = "f921a8d42391"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("tracked_emails", schema=None) as batch_op:
        batch_op.add_column(sa.Column("notify_limit", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "notify_forwarding", sa.Boolean(), server_default=sa.text("true"), nullable=False
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("tracked_emails", schema=None) as batch_op:
        batch_op.drop_column("notify_forwarding")
        batch_op.drop_column("notify_limit")
