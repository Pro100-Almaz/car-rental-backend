from sqlalchemy import UUID, Column, DateTime, ForeignKey, Integer, Numeric, Table
from sqlalchemy.orm import composite

from app.core.common.entities.rental_service import RentalService
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry

rental_services_table = Table(
    "rental_services",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "rental_id",
        UUID(as_uuid=True),
        ForeignKey("rentals.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "service_id",
        UUID(as_uuid=True),
        ForeignKey("additional_services.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("quantity", Integer, nullable=False, server_default="1"),
    Column("price", Numeric(10, 2), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_rental_services_table() -> None:
    mapper_registry.map_imperatively(
        RentalService,
        rental_services_table,
        properties={
            "id_": rental_services_table.c.id,
            "rental_id": rental_services_table.c.rental_id,
            "service_id": rental_services_table.c.service_id,
            "quantity": rental_services_table.c.quantity,
            "price": rental_services_table.c.price,
            "_created_at": composite(UtcDatetime, rental_services_table.c.created_at),
        },
        column_prefix="__",
    )
