from enum import StrEnum

from sqlalchemy import UUID, Column, DateTime, Enum, ForeignKey, Index, Numeric, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import composite

from app.core.common.entities.transaction import Transaction
from app.core.common.entities.types_ import (
    PaymentMethod,
    TransactionStatus,
    TransactionType,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


transactions_table = Table(
    "transactions",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "rental_id",
        UUID(as_uuid=True),
        ForeignKey("rentals.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "client_id",
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "type",
        Enum(
            TransactionType,
            name="transaction_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("amount", Numeric(12, 2), nullable=False),
    Column("currency", String(10), nullable=False, default="KZT"),
    Column(
        "payment_method",
        Enum(
            PaymentMethod,
            name="payment_method",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column(
        "status",
        Enum(
            TransactionStatus,
            name="transaction_status",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("external_id", String(255), nullable=True),
    Column("metadata", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("idx_transactions_org_status", "organization_id", "status"),
    Index("idx_transactions_rental", "rental_id"),
    Index("idx_transactions_client", "client_id"),
    Index("idx_transactions_external_id", "external_id", unique=True),
)


def map_transactions_table() -> None:
    mapper_registry.map_imperatively(
        Transaction,
        transactions_table,
        properties={
            "id_": transactions_table.c.id,
            "organization_id": transactions_table.c.organization_id,
            "rental_id": transactions_table.c.rental_id,
            "client_id": transactions_table.c.client_id,
            "type_": transactions_table.c.type,
            "amount": transactions_table.c.amount,
            "currency": transactions_table.c.currency,
            "payment_method": transactions_table.c.payment_method,
            "status": transactions_table.c.status,
            "external_id": transactions_table.c.external_id,
            "metadata": transactions_table.c.metadata,
            "_created_at": composite(UtcDatetime, transactions_table.c.created_at),
            "updated_at": composite(UtcDatetime, transactions_table.c.updated_at),
        },
        column_prefix="__",
    )
