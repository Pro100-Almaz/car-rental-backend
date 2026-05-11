"""add vehicles table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-09 13:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("make", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("vin", sa.String(length=17), nullable=True),
        sa.Column("license_plate", sa.String(length=20), nullable=False),
        sa.Column("color", sa.String(length=50), nullable=False),
        sa.Column(
            "category",
            sa.Enum("economy", "comfort", "business", "suv", "minivan", name="vehicle_category", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "available",
                "reserved",
                "rented",
                "returning",
                "in_service",
                "in_wash",
                "decommissioned",
                name="vehicle_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "fuel_type",
            sa.Enum("petrol", "diesel", "gas", "electric", "hybrid", name="fuel_type", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "transmission",
            sa.Enum("manual", "automatic", name="transmission", native_enum=False),
            nullable=False,
        ),
        sa.Column("current_mileage", sa.Integer(), nullable=False),
        sa.Column("purchase_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("insurance_expiry", sa.Date(), nullable=True),
        sa.Column("inspection_expiry", sa.Date(), nullable=True),
        sa.Column("gps_device_id", sa.String(length=100), nullable=True),
        sa.Column("current_latitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("current_longitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("current_fuel_level", sa.Integer(), nullable=True),
        sa.Column("branch_id", sa.UUID(), nullable=True),
        sa.Column("photos", sa.JSON(), nullable=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("pricing_override", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_vehicles_organization_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name=op.f("fk_vehicles_branch_id_branches"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vehicles")),
    )
    op.create_index(
        op.f("ix_vehicles_organization_id_status"),
        "vehicles",
        ["organization_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_vehicles_organization_id_status"), table_name="vehicles")
    op.drop_table("vehicles")
