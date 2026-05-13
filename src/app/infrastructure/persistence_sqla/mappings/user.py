from enum import StrEnum

from sqlalchemy import UUID, Boolean, Column, DateTime, Enum, ForeignKey, LargeBinary, String, Table
from sqlalchemy.orm import composite

from app.core.common.entities.types_ import UserRole
from app.core.common.entities.user import User
from app.core.common.value_objects.email import Email
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


users_table = Table(
    "users",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("email", String(Email.MAX_LEN), nullable=False, unique=True),
    Column("phone", String(20), nullable=True),
    Column("password_hash", LargeBinary, nullable=False),
    Column(
        "role",
        Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("first_name", String(100), nullable=False),
    Column("last_name", String(100), nullable=False),
    Column("is_active", Boolean, nullable=False),
    Column("email_verified", Boolean, nullable=False, server_default="false"),
    Column("last_login_at", DateTime(timezone=True), nullable=True),
    Column(
        "branch_id",
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


def map_users_table() -> None:
    mapper_registry.map_imperatively(
        User,
        users_table,
        properties={
            "id_": users_table.c.id,
            "organization_id": users_table.c.organization_id,
            "email": composite(Email, users_table.c.email),
            "phone": users_table.c.phone,
            "password_hash": users_table.c.password_hash,
            "role": users_table.c.role,
            "first_name": users_table.c.first_name,
            "last_name": users_table.c.last_name,
            "is_active": users_table.c.is_active,
            "email_verified": users_table.c.email_verified,
            "last_login_at": users_table.c.last_login_at,
            "branch_id": users_table.c.branch_id,
            "_created_at": composite(UtcDatetime, users_table.c.created_at),
            "updated_at": composite(UtcDatetime, users_table.c.updated_at),
        },
        column_prefix="__",
    )
