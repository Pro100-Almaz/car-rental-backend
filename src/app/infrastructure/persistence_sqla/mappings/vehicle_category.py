from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import composite

from app.core.common.entities.vehicle_category import VehicleCategoryEntity
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


vehicle_categories_table = Table(
    "vehicle_categories",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("name", String(100), nullable=False),
    Column("sort_order", Integer, nullable=False, default=0),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_vehicle_categories_table() -> None:
    mapper_registry.map_imperatively(
        VehicleCategoryEntity,
        vehicle_categories_table,
        properties={
            "id_": vehicle_categories_table.c.id,
            "organization_id": vehicle_categories_table.c.organization_id,
            "name": vehicle_categories_table.c.name,
            "sort_order": vehicle_categories_table.c.sort_order,
            "is_active": vehicle_categories_table.c.is_active,
            "_created_at": composite(UtcDatetime, vehicle_categories_table.c.created_at),
        },
        column_prefix="__",
    )
