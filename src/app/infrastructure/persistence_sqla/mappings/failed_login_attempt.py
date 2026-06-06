from sqlalchemy import BigInteger, Column, DateTime, Identity, Table
from sqlalchemy.dialects.postgresql import CITEXT, INET

from app.infrastructure.auth_ctx.failed_login_attempt import FailedLoginAttempt
from app.infrastructure.persistence_sqla.registry import mapper_registry

failed_login_attempts_table = Table(
    "failed_login_attempts",
    mapper_registry.metadata,
    Column("id", BigInteger(), Identity(always=False), primary_key=True),
    Column("email_lower", CITEXT(), nullable=False),
    Column("ip", INET(), nullable=False),
    Column("attempted_at", DateTime(timezone=True), nullable=False),
)


def map_failed_login_attempts_table() -> None:
    mapper_registry.map_imperatively(
        FailedLoginAttempt,
        failed_login_attempts_table,
        properties={
            "id_": failed_login_attempts_table.c.id,
            "email_lower": failed_login_attempts_table.c.email_lower,
            "ip": failed_login_attempts_table.c.ip,
            "attempted_at": failed_login_attempts_table.c.attempted_at,
        },
        column_prefix="__",
    )
