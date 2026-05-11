from sqlalchemy import UUID, Column, DateTime, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import composite

from app.core.common.entities.organization import Organization
from app.core.common.value_objects.slug import Slug
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry

organizations_table = Table(
    "organizations",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("slug", String(Slug.MAX_LEN), nullable=False, unique=True),
    Column("settings", JSONB, nullable=True),
    Column("subscription_plan", String(50), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


def map_organizations_table() -> None:
    mapper_registry.map_imperatively(
        Organization,
        organizations_table,
        properties={
            "id_": organizations_table.c.id,
            "name": organizations_table.c.name,
            "slug": composite(Slug, organizations_table.c.slug),
            "settings": organizations_table.c.settings,
            "subscription_plan": organizations_table.c.subscription_plan,
            "_created_at": composite(UtcDatetime, organizations_table.c.created_at),
            "updated_at": composite(UtcDatetime, organizations_table.c.updated_at),
        },
        column_prefix="__",
    )
