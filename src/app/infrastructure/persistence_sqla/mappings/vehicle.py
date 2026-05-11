from enum import StrEnum

from sqlalchemy import UUID, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import composite

from app.core.common.entities.types_ import FuelType, Transmission, VehicleCategory, VehicleStatus
from app.core.common.entities.vehicle import Vehicle
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


vehicles_table = Table(
    "vehicles",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("nickname", String(100), nullable=True),
    Column("make", String(100), nullable=False),
    Column("model", String(100), nullable=False),
    Column("year", Integer, nullable=False),
    Column("vin", String(17), nullable=True),
    Column("license_plate", String(20), nullable=False),
    Column("color", String(50), nullable=False),
    Column(
        "category",
        Enum(
            VehicleCategory,
            name="vehicle_category",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column(
        "status",
        Enum(
            VehicleStatus,
            name="vehicle_status",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column(
        "fuel_type",
        Enum(FuelType, name="fuel_type", native_enum=False, validate_strings=True, values_callable=get_strenum_values),
        nullable=False,
    ),
    Column(
        "transmission",
        Enum(
            Transmission,
            name="transmission",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("current_mileage", Integer, nullable=False),
    Column("purchase_price", Numeric(12, 2), nullable=True),
    Column("purchase_date", Date, nullable=True),
    Column("insurance_expiry", Date, nullable=True),
    Column("inspection_expiry", Date, nullable=True),
    Column("gps_device_id", String(100), nullable=True),
    Column("current_latitude", Numeric(10, 7), nullable=True),
    Column("current_longitude", Numeric(10, 7), nullable=True),
    Column("current_fuel_level", Integer, nullable=True),
    Column(
        "branch_id",
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("photos", JSONB, nullable=True),
    Column("features", JSONB, nullable=True),
    Column("pricing_override", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


def map_vehicles_table() -> None:
    mapper_registry.map_imperatively(
        Vehicle,
        vehicles_table,
        properties={
            "id_": vehicles_table.c.id,
            "organization_id": vehicles_table.c.organization_id,
            "nickname": vehicles_table.c.nickname,
            "make": vehicles_table.c.make,
            "model": vehicles_table.c.model,
            "year": vehicles_table.c.year,
            "vin": vehicles_table.c.vin,
            "license_plate": vehicles_table.c.license_plate,
            "color": vehicles_table.c.color,
            "category": vehicles_table.c.category,
            "status": vehicles_table.c.status,
            "fuel_type": vehicles_table.c.fuel_type,
            "transmission": vehicles_table.c.transmission,
            "current_mileage": vehicles_table.c.current_mileage,
            "purchase_price": vehicles_table.c.purchase_price,
            "purchase_date": vehicles_table.c.purchase_date,
            "insurance_expiry": vehicles_table.c.insurance_expiry,
            "inspection_expiry": vehicles_table.c.inspection_expiry,
            "gps_device_id": vehicles_table.c.gps_device_id,
            "current_latitude": vehicles_table.c.current_latitude,
            "current_longitude": vehicles_table.c.current_longitude,
            "current_fuel_level": vehicles_table.c.current_fuel_level,
            "branch_id": vehicles_table.c.branch_id,
            "photos": vehicles_table.c.photos,
            "features": vehicles_table.c.features,
            "pricing_override": vehicles_table.c.pricing_override,
            "_created_at": composite(UtcDatetime, vehicles_table.c.created_at),
            "updated_at": composite(UtcDatetime, vehicles_table.c.updated_at),
        },
        column_prefix="__",
    )
