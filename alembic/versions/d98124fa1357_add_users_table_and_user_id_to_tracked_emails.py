"""add users table and user_id to tracked_emails

Revision ID: d98124fa1357
Revises: c57a24e931b2
Create Date: 2026-08-15 12:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "d98124fa1357"
down_revision: Union[str, None] = "c57a24e931b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_chat_id", sa.String(length=64), nullable=False),
        sa.Column("telegram_username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=32), nullable=True),
        sa.Column("default_notify_limit", sa.Integer(), nullable=True),
        sa.Column(
            "default_notify_forwarding",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("timezone", sa.String(length=64), server_default="UTC", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_active_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_telegram_chat_id", "users", ["telegram_chat_id"], unique=True)

    # 2. Add user_id to tracked_emails
    with op.batch_alter_table("tracked_emails", schema=None) as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_tracked_emails_user_id", ["user_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_tracked_emails_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # 3. Data Backfill: Migrate existing telegram_chat_ids to users
    conn = op.get_bind()
    try:
        conn.execute(
            sa.text(
                """
                INSERT INTO users (telegram_chat_id, created_at, last_active_at)
                SELECT telegram_chat_id, MIN(created_at), MAX(created_at)
                FROM tracked_emails
                WHERE telegram_chat_id IS NOT NULL AND telegram_chat_id != ''
                GROUP BY telegram_chat_id
                """
            )
        )
        conn.execute(
            sa.text(
                """
                UPDATE tracked_emails
                SET user_id = (
                    SELECT users.id FROM users
                    WHERE users.telegram_chat_id = tracked_emails.telegram_chat_id
                )
                WHERE telegram_chat_id IS NOT NULL AND telegram_chat_id != ''
                """
            )
        )
    except Exception:
        # Ignore backfill errors on empty databases
        pass


def downgrade() -> None:
    with op.batch_alter_table("tracked_emails", schema=None) as batch_op:
        batch_op.drop_constraint("fk_tracked_emails_user_id_users", type_="foreignkey")
        batch_op.drop_index("ix_tracked_emails_user_id")
        batch_op.drop_column("user_id")

    op.drop_index("ix_users_telegram_chat_id", table_name="users")
    op.drop_table("users")
