from enum import StrEnum

from sqlalchemy import UUID, Boolean, Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import composite

from app.core.common.entities.client import Client
from app.core.common.entities.types_ import TrustLevel, VerificationStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


clients_table = Table(
    "clients",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    ),
    Column("phone", String(20), nullable=False),
    Column("email", String(254), nullable=True),
    Column("first_name", String(100), nullable=False),
    Column("last_name", String(100), nullable=False),
    Column("id_document_url", String(500), nullable=True),
    Column("license_front_url", String(500), nullable=True),
    Column("license_back_url", String(500), nullable=True),
    Column(
        "verification_status",
        Enum(
            VerificationStatus,
            name="verification_status",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("trust_score", Integer, nullable=False, default=0),
    Column(
        "trust_level",
        Enum(
            TrustLevel,
            name="trust_level",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("is_blacklisted", Boolean, nullable=False, default=False),
    Column("blacklist_reason", Text, nullable=True),
    Column("wallet_balance", Numeric(12, 2), nullable=False, default=0),
    Column("debt_balance", Numeric(12, 2), nullable=False, default=0),
    Column("metadata", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


def map_clients_table() -> None:
    mapper_registry.map_imperatively(
        Client,
        clients_table,
        properties={
            "id_": clients_table.c.id,
            "organization_id": clients_table.c.organization_id,
            "user_id": clients_table.c.user_id,
            "phone": clients_table.c.phone,
            "email": clients_table.c.email,
            "first_name": clients_table.c.first_name,
            "last_name": clients_table.c.last_name,
            "id_document_url": clients_table.c.id_document_url,
            "license_front_url": clients_table.c.license_front_url,
            "license_back_url": clients_table.c.license_back_url,
            "verification_status": clients_table.c.verification_status,
            "trust_score": clients_table.c.trust_score,
            "trust_level": clients_table.c.trust_level,
            "is_blacklisted": clients_table.c.is_blacklisted,
            "blacklist_reason": clients_table.c.blacklist_reason,
            "wallet_balance": clients_table.c.wallet_balance,
            "debt_balance": clients_table.c.debt_balance,
            "metadata": clients_table.c.metadata,
            "_created_at": composite(UtcDatetime, clients_table.c.created_at),
            "updated_at": composite(UtcDatetime, clients_table.c.updated_at),
        },
        column_prefix="__",
    )
