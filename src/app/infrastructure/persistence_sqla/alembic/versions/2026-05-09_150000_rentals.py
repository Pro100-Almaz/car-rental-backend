"""Create rentals table.

Revision ID: 6b5c4d3e2f1a
Revises: 5a4c3b2d1e0f
Create Date: 2026-05-09 15:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6b5c4d3e2f1a"
down_revision: str | None = "5a4c3b2d1e0f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rentals",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "manager_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("booking_type", sa.String(20), nullable=False),
        # Timing
        sa.Column("booked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True),
        # Pricing
        sa.Column("base_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("rate_type", sa.String(20), nullable=False),
        sa.Column("estimated_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("actual_total", sa.Numeric(10, 2), nullable=True),
        sa.Column("discount_code", sa.String(50), nullable=True),
        sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("late_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("mileage_surcharge", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("fuel_charge", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("wash_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("damage_charge", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("fine_charge", sa.Numeric(10, 2), nullable=False, server_default="0"),
        # Deposit
        sa.Column("deposit_type", sa.String(20), nullable=False),
        sa.Column("deposit_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("deposit_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("deposit_refund_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        # Inspection
        sa.Column("checkin_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("checkout_data", sa.dialects.postgresql.JSONB, nullable=True),
        # Final
        sa.Column("invoice_url", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_rentals_org_status", "rentals", ["organization_id", "status"])
    op.create_index("idx_rentals_vehicle", "rentals", ["vehicle_id", "status"])
    op.create_index("idx_rentals_client", "rentals", ["client_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_rentals_client")
    op.drop_index("idx_rentals_vehicle")
    op.drop_index("idx_rentals_org_status")
    op.drop_table("rentals")
