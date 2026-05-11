"""Add missing spec fields: vehicle.nickname, rental.cancellation_reason/prepayment

Revision ID: af1b2c3d4e5f
Revises: 9e8f7a6b5c4d
Create Date: 2026-05-10 12:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "af1b2c3d4e5f"
down_revision: str | None = "9e8f7a6b5c4d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("vehicles", sa.Column("nickname", sa.String(100), nullable=True))

    op.add_column("rentals", sa.Column("cancellation_reason", sa.Text(), nullable=True))
    op.add_column(
        "rentals",
        sa.Column("prepayment_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "rentals",
        sa.Column("prepayment_status", sa.String(10), nullable=False, server_default="none"),
    )


def downgrade() -> None:
    op.drop_column("rentals", "prepayment_status")
    op.drop_column("rentals", "prepayment_amount")
    op.drop_column("rentals", "cancellation_reason")
    op.drop_column("vehicles", "nickname")
