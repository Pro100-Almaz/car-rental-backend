"""fines

Revision ID: 8d7e6f5a4b3c
Revises: 7c6d5e4f3a2b
Create Date: 2026-05-10 10:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8d7e6f5a4b3c"
down_revision: str | None = "7c6d5e4f3a2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fines",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("vehicle_id", sa.UUID(), nullable=False),
        sa.Column("rental_id", sa.UUID(), nullable=True),
        sa.Column("client_id", sa.UUID(), nullable=True),
        sa.Column("fine_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("fine_date", sa.Date(), nullable=False),
        sa.Column("document_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["rental_id"], ["rentals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_fines_vehicle_date", "fines", ["vehicle_id", "fine_date"])
    op.create_index("idx_fines_org_status", "fines", ["organization_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_fines_org_status", table_name="fines")
    op.drop_index("idx_fines_vehicle_date", table_name="fines")
    op.drop_table("fines")
