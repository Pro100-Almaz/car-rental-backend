from sqlalchemy import UUID, Column, DateTime, ForeignKey, Table

from app.infrastructure.auth_ctx.revoked_access_jti import RevokedAccessJti
from app.infrastructure.persistence_sqla.registry import mapper_registry

revoked_access_jtis_table = Table(
    "revoked_access_jtis",
    mapper_registry.metadata,
    Column("jti", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)


def map_revoked_access_jtis_table() -> None:
    mapper_registry.map_imperatively(
        RevokedAccessJti,
        revoked_access_jtis_table,
        properties={
            "jti": revoked_access_jtis_table.c.jti,
            "user_id": revoked_access_jtis_table.c.user_id,
            "expires_at": revoked_access_jtis_table.c.expires_at,
        },
        column_prefix="__",
    )
