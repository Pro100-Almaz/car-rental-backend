from sqlalchemy import UUID, Column, Date, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import composite

from app.core.common.entities.vehicle_document import VehicleDocument
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


vehicle_documents_table = Table(
    "vehicle_documents",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "vehicle_id",
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("document_type", String(50), nullable=False),
    Column("name", String(255), nullable=False),
    Column("url", String(500), nullable=False),
    Column("expiry_date", Date, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_vehicle_documents_table() -> None:
    mapper_registry.map_imperatively(
        VehicleDocument,
        vehicle_documents_table,
        properties={
            "id_": vehicle_documents_table.c.id,
            "vehicle_id": vehicle_documents_table.c.vehicle_id,
            "document_type": vehicle_documents_table.c.document_type,
            "name": vehicle_documents_table.c.name,
            "url": vehicle_documents_table.c.url,
            "expiry_date": vehicle_documents_table.c.expiry_date,
            "_created_at": composite(UtcDatetime, vehicle_documents_table.c.created_at),
        },
        column_prefix="__",
    )
