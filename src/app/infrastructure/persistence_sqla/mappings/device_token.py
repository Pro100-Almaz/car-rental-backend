from enum import StrEnum

from sqlalchemy import UUID, Column, DateTime, Enum, ForeignKey, String, Table
from sqlalchemy.orm import composite

from app.core.common.entities.device_token import DeviceToken
from app.core.common.entities.types_ import DevicePlatform
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


device_tokens_table = Table(
    "device_tokens",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("token", String(500), nullable=False, unique=True),
    Column(
        "platform",
        Enum(
            DevicePlatform,
            name="device_platform",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("device_name", String(200), nullable=True),
    Column("last_active_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_device_tokens_table() -> None:
    mapper_registry.map_imperatively(
        DeviceToken,
        device_tokens_table,
        properties={
            "id_": device_tokens_table.c.id,
            "user_id": device_tokens_table.c.user_id,
            "token": device_tokens_table.c.token,
            "platform": device_tokens_table.c.platform,
            "device_name": device_tokens_table.c.device_name,
            "last_active_at": composite(UtcDatetime, device_tokens_table.c.last_active_at),
            "_created_at": composite(UtcDatetime, device_tokens_table.c.created_at),
        },
        column_prefix="__",
    )
