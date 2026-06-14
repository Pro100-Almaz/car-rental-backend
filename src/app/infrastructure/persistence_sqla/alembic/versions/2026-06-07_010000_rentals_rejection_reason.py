"""Add rejection_reason column to rentals table.

Revision ID: r3j3c7i0n001
Revises: j7w7t7a7u7th
Create Date: 2026-06-07 01:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "r3j3c7i0n001"
down_revision: str | None = "j7w7t7a7u7th"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("rentals", sa.Column("rejection_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("rentals", "rejection_reason")
