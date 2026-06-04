from enum import StrEnum

from sqlalchemy import UUID, Boolean, Column, DateTime, Enum, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import composite

from app.core.common.entities.notification import Notification
from app.core.common.entities.types_ import NotificationType
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


notifications_table = Table(
    "notifications",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "type",
        Enum(
            NotificationType,
            name="notification_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("title", String(255), nullable=False),
    Column("body", Text, nullable=False),
    Column("deep_link", String(500), nullable=True),
    Column("metadata", JSONB, nullable=True),
    Column("is_read", Boolean, nullable=False, server_default="false"),
    Column("read_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_notifications_table() -> None:
    mapper_registry.map_imperatively(
        Notification,
        notifications_table,
        properties={
            "id_": notifications_table.c.id,
            "user_id": notifications_table.c.user_id,
            "organization_id": notifications_table.c.organization_id,
            "type_": notifications_table.c.type,
            "title": notifications_table.c.title,
            "body": notifications_table.c.body,
            "deep_link": notifications_table.c.deep_link,
            "metadata": notifications_table.c.metadata,
            "is_read": notifications_table.c.is_read,
            "read_at": composite(UtcDatetime, notifications_table.c.read_at),
            "_created_at": composite(UtcDatetime, notifications_table.c.created_at),
        },
        column_prefix="__",
    )
