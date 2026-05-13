"""investors, vehicle_investors, investor_payouts tables

Revision ID: d4e5f6a7b8c9
Revises: af1b2c3d4e5f
Create Date: 2026-05-10 13:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "af1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investors",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "own",
                "partner",
                "shared",
                name="investor_type",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("contact_phone", sa.String(20), nullable=True),
        sa.Column("contact_email", sa.String(200), nullable=True),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "vehicle_investors",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "vehicle_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "investor_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("investors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("share_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "profit_distribution_type",
            sa.Enum(
                "fixed",
                "percentage",
                name="profit_distribution_type",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "investor_payouts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "investor_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("investors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_month", sa.Date, nullable=False),
        sa.Column("calculated_profit", sa.Numeric(12, 2), nullable=False),
        sa.Column("share_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "calculated",
                "approved",
                "paid",
                name="payout_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("investor_payouts")
    op.drop_table("vehicle_investors")
    op.drop_table("investors")
