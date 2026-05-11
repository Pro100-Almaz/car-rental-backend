from enum import StrEnum

from sqlalchemy import UUID, Column, DateTime, Enum, ForeignKey, Index, Numeric, Table, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import composite

from app.core.common.entities.service_task import ServiceTask
from app.core.common.entities.types_ import ServiceTaskType, TaskPriority, TaskStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


service_tasks_table = Table(
    "service_tasks",
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
        "assigned_to",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "task_type",
        Enum(
            ServiceTaskType,
            name="service_task_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column(
        "priority",
        Enum(
            TaskPriority,
            name="task_priority",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column(
        "status",
        Enum(
            TaskStatus,
            name="task_status",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("description", Text, nullable=True),
    Column("estimated_cost", Numeric(10, 2), nullable=True),
    Column("actual_cost", Numeric(10, 2), nullable=True),
    Column("proof_photos", JSONB, nullable=True),
    Column("notes", Text, nullable=True),
    Column("due_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("idx_service_tasks_vehicle_status", "vehicle_id", "status"),
    Index("idx_service_tasks_assigned_status", "assigned_to", "status"),
    Index("idx_service_tasks_org_status", "organization_id", "status"),
)


def map_service_tasks_table() -> None:
    mapper_registry.map_imperatively(
        ServiceTask,
        service_tasks_table,
        properties={
            "id_": service_tasks_table.c.id,
            "organization_id": service_tasks_table.c.organization_id,
            "vehicle_id": service_tasks_table.c.vehicle_id,
            "rental_id": service_tasks_table.c.rental_id,
            "assigned_to": service_tasks_table.c.assigned_to,
            "task_type": service_tasks_table.c.task_type,
            "priority": service_tasks_table.c.priority,
            "status": service_tasks_table.c.status,
            "description": service_tasks_table.c.description,
            "estimated_cost": service_tasks_table.c.estimated_cost,
            "actual_cost": service_tasks_table.c.actual_cost,
            "proof_photos": service_tasks_table.c.proof_photos,
            "notes": service_tasks_table.c.notes,
            "due_at": service_tasks_table.c.due_at,
            "completed_at": service_tasks_table.c.completed_at,
            "_created_at": composite(UtcDatetime, service_tasks_table.c.created_at),
            "updated_at": composite(UtcDatetime, service_tasks_table.c.updated_at),
        },
        column_prefix="__",
    )
