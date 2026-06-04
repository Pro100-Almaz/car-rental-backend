"""Sprint 2: Mobile vehicle browsing & booking — rental source/pickup_notes fields.

Revision ID: s2p2r2i2n2t2
Revises: m1n2o3p4q5r6
Create Date: 2026-05-22 02:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "s2p2r2i2n2t2"
down_revision = "m1n2o3p4q5r6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rentals",
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
    )
    op.add_column(
        "rentals",
        sa.Column("pickup_notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("rentals", "pickup_notes")
    op.drop_column("rentals", "source")
