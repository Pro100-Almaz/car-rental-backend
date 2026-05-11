from sqlalchemy import UUID, Column, DateTime, ForeignKey, Numeric, String, Table
from sqlalchemy.orm import composite

from app.core.common.entities.branch import Branch
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry

branches_table = Table(
    "branches",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("name", String(255), nullable=False),
    Column("address", String(500), nullable=False),
    Column("latitude", Numeric(10, 7), nullable=True),
    Column("longitude", Numeric(10, 7), nullable=True),
    Column("timezone", String(50), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_branches_table() -> None:
    mapper_registry.map_imperatively(
        Branch,
        branches_table,
        properties={
            "id_": branches_table.c.id,
            "organization_id": branches_table.c.organization_id,
            "name": branches_table.c.name,
            "address": branches_table.c.address,
            "latitude": branches_table.c.latitude,
            "longitude": branches_table.c.longitude,
            "timezone": branches_table.c.timezone,
            "_created_at": composite(UtcDatetime, branches_table.c.created_at),
        },
        column_prefix="__",
    )
