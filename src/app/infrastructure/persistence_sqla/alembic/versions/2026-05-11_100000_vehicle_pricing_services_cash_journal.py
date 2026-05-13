"""vehicle_pricing, additional_services, rental_services, expense_categories, cash_journal tables

Revision ID: c3d4e5f6a7b8
Revises: d4e5f6a7b8c9
Create Date: 2026-05-11 10:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vehicle_pricing",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "vehicle_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("base_daily_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("multiplier", sa.Numeric(4, 2), nullable=False, server_default="1.0"),
        sa.Column("valid_from", sa.Date, nullable=False),
        sa.Column("valid_to", sa.Date, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "additional_services",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "rental_services",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rental_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("rentals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "service_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("additional_services.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "expense_categories",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "type",
            sa.Enum("direct", "overhead", name="expense_category_type", native_enum=False),
            nullable=False,
        ),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cash_journal",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column(
            "operation_type",
            sa.Enum("income", "expense", name="operation_type", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "rental_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("rentals.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "expense_category_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("expense_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "payment_method",
            sa.Enum(
                "kaspi",
                "card",
                "cash",
                "wallet",
                "bank_transfer",
                name="journal_payment_method",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("receipt_url", sa.String(500), nullable=True),
        sa.Column(
            "confirmed_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("cash_journal")
    op.drop_table("expense_categories")
    op.drop_table("rental_services")
    op.drop_table("additional_services")
    op.drop_table("vehicle_pricing")
