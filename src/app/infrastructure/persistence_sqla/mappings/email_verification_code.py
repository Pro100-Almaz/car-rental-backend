from sqlalchemy import UUID, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import composite

from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.auth_ctx.verification_code import EmailVerificationCode
from app.infrastructure.persistence_sqla.registry import mapper_registry

email_verification_codes_table = Table(
    "email_verification_codes",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("code", String(6), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_email_verification_codes_table() -> None:
    mapper_registry.map_imperatively(
        EmailVerificationCode,
        email_verification_codes_table,
        properties={
            "id_": email_verification_codes_table.c.id,
            "user_id": email_verification_codes_table.c.user_id,
            "code": email_verification_codes_table.c.code,
            "expires_at": composite(UtcDatetime, email_verification_codes_table.c.expires_at),
            "created_at": composite(UtcDatetime, email_verification_codes_table.c.created_at),
        },
        column_prefix="__",
    )
