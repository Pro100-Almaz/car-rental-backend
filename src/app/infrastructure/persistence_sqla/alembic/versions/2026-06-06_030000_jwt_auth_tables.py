"""JWT auth: add refresh_tokens, revoked_access_jtis, failed_login_attempts; drop auth_sessions.

Revision ID: j7w7t7a7u7th
Revises: d8r8o8p8d8u8
Create Date: 2026-06-06 03:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "j7w7t7a7u7th"
down_revision: str | None = "d8r8o8p8d8u8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # email_lower in failed_login_attempts is case-insensitive: require the citext extension.
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("issued_access_jti", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        # replaced_by FKs back to refresh_tokens.id — added below via op.create_foreign_key
        # so the self-reference is created after the table exists.
        sa.Column("replaced_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
    )
    op.create_foreign_key(
        "fk_refresh_tokens_replaced_by_refresh_tokens",
        "refresh_tokens",
        "refresh_tokens",
        ["replaced_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    op.create_table(
        "revoked_access_jtis",
        sa.Column("jti", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_revoked_access_jtis_expires_at", "revoked_access_jtis", ["expires_at"])

    op.create_table(
        "failed_login_attempts",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("email_lower", postgresql.CITEXT(), nullable=False),
        sa.Column("ip", postgresql.INET(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_failed_login_attempts_email_lower", "failed_login_attempts", ["email_lower"])
    op.create_index("ix_failed_login_attempts_ip", "failed_login_attempts", ["ip"])
    op.create_index("ix_failed_login_attempts_attempted_at", "failed_login_attempts", ["attempted_at"])

    # Cookie auth is being dropped in the same release; auth_sessions has no incoming FKs.
    op.drop_table("auth_sessions")


def downgrade() -> None:
    # Restore auth_sessions schema (data not preserved).
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expiration", sa.DateTime(timezone=True), nullable=False),
    )

    op.drop_index("ix_failed_login_attempts_attempted_at", table_name="failed_login_attempts")
    op.drop_index("ix_failed_login_attempts_ip", table_name="failed_login_attempts")
    op.drop_index("ix_failed_login_attempts_email_lower", table_name="failed_login_attempts")
    op.drop_table("failed_login_attempts")

    op.drop_index("ix_revoked_access_jtis_expires_at", table_name="revoked_access_jtis")
    op.drop_table("revoked_access_jtis")

    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_constraint("fk_refresh_tokens_replaced_by_refresh_tokens", "refresh_tokens", type_="foreignkey")
    op.drop_table("refresh_tokens")

    # citext extension left in place — other migrations / future work may need it.
