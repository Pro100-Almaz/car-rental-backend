from enum import StrEnum

from sqlalchemy import UUID, Column, DateTime, Enum, ForeignKey, String, Table, Text
from sqlalchemy.orm import composite

from app.core.common.entities.investor import Investor
from app.core.common.entities.types_ import InvestorType
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


investors_table = Table(
    "investors",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("full_name", String(200), nullable=False),
    Column(
        "type",
        Enum(
            InvestorType,
            name="investor_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("contact_phone", String(20), nullable=True),
    Column("contact_email", String(200), nullable=True),
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("notes", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


def map_investors_table() -> None:
    mapper_registry.map_imperatively(
        Investor,
        investors_table,
        properties={
            "id_": investors_table.c.id,
            "organization_id": investors_table.c.organization_id,
            "full_name": investors_table.c.full_name,
            "type_": investors_table.c.type,
            "contact_phone": investors_table.c.contact_phone,
            "contact_email": investors_table.c.contact_email,
            "user_id": investors_table.c.user_id,
            "notes": investors_table.c.notes,
            "_created_at": composite(UtcDatetime, investors_table.c.created_at),
            "updated_at": composite(UtcDatetime, investors_table.c.updated_at),
        },
        column_prefix="__",
    )
