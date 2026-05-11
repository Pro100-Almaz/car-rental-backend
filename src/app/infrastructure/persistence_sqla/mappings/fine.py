from enum import StrEnum

from sqlalchemy import UUID, Column, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Table, Text
from sqlalchemy.orm import composite

from app.core.common.entities.fine import Fine
from app.core.common.entities.types_ import FineStatus, FineType
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


fines_table = Table(
    "fines",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "vehicle_id",
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "rental_id",
        UUID(as_uuid=True),
        ForeignKey("rentals.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "client_id",
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "fine_type",
        Enum(
            FineType,
            name="fine_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("amount", Numeric(10, 2), nullable=False),
    Column("description", Text, nullable=True),
    Column("fine_date", Date, nullable=False),
    Column("document_url", String(500), nullable=True),
    Column(
        "status",
        Enum(
            FineStatus,
            name="fine_status",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("idx_fines_vehicle_date", "vehicle_id", "fine_date"),
    Index("idx_fines_org_status", "organization_id", "status"),
)


def map_fines_table() -> None:
    mapper_registry.map_imperatively(
        Fine,
        fines_table,
        properties={
            "id_": fines_table.c.id,
            "organization_id": fines_table.c.organization_id,
            "vehicle_id": fines_table.c.vehicle_id,
            "rental_id": fines_table.c.rental_id,
            "client_id": fines_table.c.client_id,
            "fine_type": fines_table.c.fine_type,
            "amount": fines_table.c.amount,
            "description": fines_table.c.description,
            "fine_date": fines_table.c.fine_date,
            "document_url": fines_table.c.document_url,
            "status": fines_table.c.status,
            "_created_at": composite(UtcDatetime, fines_table.c.created_at),
            "updated_at": composite(UtcDatetime, fines_table.c.updated_at),
        },
        column_prefix="__",
    )
