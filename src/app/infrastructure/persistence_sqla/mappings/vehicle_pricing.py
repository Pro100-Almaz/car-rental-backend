from sqlalchemy import UUID, Boolean, Column, Date, DateTime, ForeignKey, Numeric, String, Table
from sqlalchemy.orm import composite

from app.core.common.entities.vehicle_pricing import VehiclePricing
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry

vehicle_pricing_table = Table(
    "vehicle_pricing",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "vehicle_id",
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("base_daily_rate", Numeric(10, 2), nullable=False),
    Column("name", String(200), nullable=False),
    Column("multiplier", Numeric(4, 2), nullable=False),
    Column("valid_from", Date, nullable=False),
    Column("valid_to", Date, nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_vehicle_pricing_table() -> None:
    mapper_registry.map_imperatively(
        VehiclePricing,
        vehicle_pricing_table,
        properties={
            "id_": vehicle_pricing_table.c.id,
            "vehicle_id": vehicle_pricing_table.c.vehicle_id,
            "base_daily_rate": vehicle_pricing_table.c.base_daily_rate,
            "name": vehicle_pricing_table.c.name,
            "multiplier": vehicle_pricing_table.c.multiplier,
            "valid_from": vehicle_pricing_table.c.valid_from,
            "valid_to": vehicle_pricing_table.c.valid_to,
            "is_active": vehicle_pricing_table.c.is_active,
            "_created_at": composite(UtcDatetime, vehicle_pricing_table.c.created_at),
        },
        column_prefix="__",
    )
