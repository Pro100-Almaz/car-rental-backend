from sqlalchemy import UUID, Column, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import composite

from app.core.common.entities.client_organization import ClientOrganization
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry

client_organizations_table = Table(
    "client_organizations",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "client_id",
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("joined_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("client_id", "organization_id", name="uq_client_organization"),
)


def map_client_organizations_table() -> None:
    mapper_registry.map_imperatively(
        ClientOrganization,
        client_organizations_table,
        properties={
            "id_": client_organizations_table.c.id,
            "client_id": client_organizations_table.c.client_id,
            "organization_id": client_organizations_table.c.organization_id,
            "_joined_at": composite(UtcDatetime, client_organizations_table.c.joined_at),
        },
        column_prefix="__",
    )
