from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKey, Numeric, String, Table
from sqlalchemy.orm import composite

from app.core.common.entities.additional_service import AdditionalService
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry

additional_services_table = Table(
    "additional_services",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("name", String(200), nullable=False),
    Column("price", Numeric(10, 2), nullable=False),
    Column("is_active", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_additional_services_table() -> None:
    mapper_registry.map_imperatively(
        AdditionalService,
        additional_services_table,
        properties={
            "id_": additional_services_table.c.id,
            "organization_id": additional_services_table.c.organization_id,
            "name": additional_services_table.c.name,
            "price": additional_services_table.c.price,
            "is_active": additional_services_table.c.is_active,
            "_created_at": composite(UtcDatetime, additional_services_table.c.created_at),
        },
        column_prefix="__",
    )
