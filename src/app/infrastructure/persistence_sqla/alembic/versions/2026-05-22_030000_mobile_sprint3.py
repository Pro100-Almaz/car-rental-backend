"""Sprint 3: Mobile payments — transaction source/client_note/rejection_reason fields.

Revision ID: s3p3r3i3n3t3
Revises: s2p2r2i2n2t2
Create Date: 2026-05-22 03:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "s3p3r3i3n3t3"
down_revision = "s2p2r2i2n2t2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
    )
    op.add_column(
        "transactions",
        sa.Column("client_note", sa.String(2000), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("rejection_reason", sa.String(2000), nullable=True),
    )
    op.create_index(
        "idx_transactions_client_status",
        "transactions",
        ["client_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_transactions_client_status", table_name="transactions")
    op.drop_column("transactions", "rejection_reason")
    op.drop_column("transactions", "client_note")
    op.drop_column("transactions", "source")
