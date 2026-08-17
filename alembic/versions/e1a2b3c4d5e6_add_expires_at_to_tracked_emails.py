"""add expires_at to tracked_emails

Revision ID: e1a2b3c4d5e6
Revises: d98124fa1357
Create Date: 2026-08-16 11:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, None] = "d98124fa1357"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("tracked_emails", schema=None) as batch_op:
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tracked_emails", schema=None) as batch_op:
        batch_op.drop_column("expires_at")
