from sqlalchemy import UUID, Column, DateTime, Enum, ForeignKey, String, Table
from sqlalchemy.orm import composite

from app.core.common.entities.types_ import UserRole
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.auth_ctx.invite import Invite
from app.infrastructure.persistence_sqla.mappings.user import get_strenum_values
from app.infrastructure.persistence_sqla.registry import mapper_registry

invites_table = Table(
    "invites",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("email", String(320), nullable=False),
    Column(
        "role",
        Enum(
            UserRole,
            name="invite_role",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("token", String(64), nullable=False, unique=True, index=True),
    Column(
        "invited_by",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("used_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_invites_table() -> None:
    mapper_registry.map_imperatively(
        Invite,
        invites_table,
        properties={
            "id_": invites_table.c.id,
            "organization_id": invites_table.c.organization_id,
            "email": invites_table.c.email,
            "role": invites_table.c.role,
            "token": invites_table.c.token,
            "invited_by": invites_table.c.invited_by,
            "expires_at": composite(UtcDatetime, invites_table.c.expires_at),
            "used_at": composite(UtcDatetime, invites_table.c.used_at),
            "created_at": composite(UtcDatetime, invites_table.c.created_at),
        },
        column_prefix="__",
    )
