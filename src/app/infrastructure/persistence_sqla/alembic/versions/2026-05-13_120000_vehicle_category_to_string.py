"""Change vehicles.category from enum to plain string.

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-05-13 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "j0k1l2m3n4o5"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "vehicles",
        "category",
        type_=sa.String(100),
        existing_type=sa.String(100),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "vehicles",
        "category",
        type_=sa.String(100),
        existing_type=sa.String(100),
        existing_nullable=False,
    )
