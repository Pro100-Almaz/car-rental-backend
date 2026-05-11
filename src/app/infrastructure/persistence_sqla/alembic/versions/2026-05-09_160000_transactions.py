"""transactions

Revision ID: 7c6d5e4f3a2b
Revises: 6b5c4d3e2f1a
Create Date: 2026-05-09 16:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7c6d5e4f3a2b"
down_revision: str | None = "6b5c4d3e2f1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("rental_id", sa.UUID(), nullable=True),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="KZT"),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rental_id"], ["rentals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_transactions_org_status", "transactions", ["organization_id", "status"])
    op.create_index("idx_transactions_rental", "transactions", ["rental_id"])
    op.create_index("idx_transactions_client", "transactions", ["client_id"])
    op.create_index("idx_transactions_external_id", "transactions", ["external_id"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_transactions_external_id", table_name="transactions")
    op.drop_index("idx_transactions_client", table_name="transactions")
    op.drop_index("idx_transactions_rental", table_name="transactions")
    op.drop_index("idx_transactions_org_status", table_name="transactions")
    op.drop_table("transactions")
