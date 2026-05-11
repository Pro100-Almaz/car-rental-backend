"""Create clients table.

Revision ID: 5a4c3b2d1e0f
Revises: b2c3d4e5f6a7
Create Date: 2026-05-09 14:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5a4c3b2d1e0f"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("id_document_url", sa.String(500), nullable=True),
        sa.Column("license_front_url", sa.String(500), nullable=True),
        sa.Column("license_back_url", sa.String(500), nullable=True),
        sa.Column("verification_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("trust_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("trust_level", sa.String(20), nullable=False, server_default="new"),
        sa.Column("is_blacklisted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("blacklist_reason", sa.Text, nullable=True),
        sa.Column("wallet_balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("debt_balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("metadata", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_clients_org_id", "clients", ["organization_id"])
    op.create_index("idx_clients_phone", "clients", ["organization_id", "phone"], unique=True)
    op.create_index("idx_clients_verification", "clients", ["organization_id", "verification_status"])


def downgrade() -> None:
    op.drop_index("idx_clients_verification")
    op.drop_index("idx_clients_phone")
    op.drop_index("idx_clients_org_id")
    op.drop_table("clients")
