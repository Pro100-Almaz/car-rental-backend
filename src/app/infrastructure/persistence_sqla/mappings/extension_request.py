from enum import StrEnum

from sqlalchemy import UUID, Column, DateTime, Enum, ForeignKey, Numeric, String, Table
from sqlalchemy.orm import composite

from app.core.common.entities.extension_request import ExtensionRequest
from app.core.common.entities.types_ import ExtensionRequestStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


extension_requests_table = Table(
    "extension_requests",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "rental_id",
        UUID(as_uuid=True),
        ForeignKey("rentals.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "client_id",
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("new_end_date", DateTime(timezone=True), nullable=False),
    Column("additional_cost", Numeric(12, 2), nullable=False),
    Column(
        "status",
        Enum(
            ExtensionRequestStatus,
            name="extension_request_status",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
        server_default="pending",
    ),
    Column("rejection_reason", String(2000), nullable=True),
    Column("reviewed_by", UUID(as_uuid=True), ForeignKey("users.id"), nullable=True),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_extension_requests_table() -> None:
    mapper_registry.map_imperatively(
        ExtensionRequest,
        extension_requests_table,
        properties={
            "id_": extension_requests_table.c.id,
            "organization_id": extension_requests_table.c.organization_id,
            "rental_id": extension_requests_table.c.rental_id,
            "client_id": extension_requests_table.c.client_id,
            "new_end_date": composite(UtcDatetime, extension_requests_table.c.new_end_date),
            "additional_cost": extension_requests_table.c.additional_cost,
            "status": extension_requests_table.c.status,
            "rejection_reason": extension_requests_table.c.rejection_reason,
            "reviewed_by": extension_requests_table.c.reviewed_by,
            "reviewed_at": composite(UtcDatetime, extension_requests_table.c.reviewed_at),
            "_created_at": composite(UtcDatetime, extension_requests_table.c.created_at),
        },
        column_prefix="__",
    )
