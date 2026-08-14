from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e87081ab1b99"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tracked_emails",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("recipient_name", sa.String(length=255), nullable=True),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("open_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("tracked_emails", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_tracked_emails_token"), ["token"], unique=True)

    op.create_table(
        "open_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.String(length=128), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum("HUMAN_OPEN", "BOT_SCANNER", "PROXY_PREFETCH", name="event_type_enum"),
            nullable=False,
        ),
        sa.Column("elapsed_seconds", sa.Float(), nullable=True),
        sa.Column("raw_headers", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["email_id"], ["tracked_emails.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("open_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_open_events_email_id"), ["email_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("open_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_open_events_email_id"))

    op.drop_table("open_events")
    with op.batch_alter_table("tracked_emails", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_tracked_emails_token"))

    op.drop_table("tracked_emails")
