from sqlalchemy import UUID, BigInteger, Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import INET

from app.infrastructure.auth_ctx.refresh_token import RefreshToken
from app.infrastructure.persistence_sqla.registry import mapper_registry

refresh_tokens_table = Table(
    "refresh_tokens",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("family_id", UUID(as_uuid=True), nullable=False),
    Column("token_hash", Text(), nullable=False, unique=True),
    Column("issued_access_jti", UUID(as_uuid=True), nullable=True),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True), nullable=True),
    Column("replaced_by", UUID(as_uuid=True), ForeignKey("refresh_tokens.id", ondelete="SET NULL"), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("last_used_at", DateTime(timezone=True), nullable=True),
    Column("ip", INET(), nullable=True),
    Column("user_agent", String(512), nullable=True),
)

_ = BigInteger  # silence unused-import on platforms without it


def map_refresh_tokens_table() -> None:
    mapper_registry.map_imperatively(
        RefreshToken,
        refresh_tokens_table,
        properties={
            "id_": refresh_tokens_table.c.id,
            "user_id": refresh_tokens_table.c.user_id,
            "family_id": refresh_tokens_table.c.family_id,
            "token_hash": refresh_tokens_table.c.token_hash,
            "issued_access_jti": refresh_tokens_table.c.issued_access_jti,
            "expires_at": refresh_tokens_table.c.expires_at,
            "revoked_at": refresh_tokens_table.c.revoked_at,
            "replaced_by": refresh_tokens_table.c.replaced_by,
            "created_at": refresh_tokens_table.c.created_at,
            "last_used_at": refresh_tokens_table.c.last_used_at,
            "ip": refresh_tokens_table.c.ip,
            "user_agent": refresh_tokens_table.c.user_agent,
        },
        column_prefix="__",
    )
