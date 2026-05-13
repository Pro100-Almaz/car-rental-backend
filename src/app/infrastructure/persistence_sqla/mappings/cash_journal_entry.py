from enum import StrEnum

from sqlalchemy import UUID, Column, Date, DateTime, Enum, ForeignKey, Numeric, String, Table, Text
from sqlalchemy.orm import composite

from app.core.common.entities.cash_journal_entry import CashJournalEntry
from app.core.common.entities.types_ import OperationType, PaymentMethod
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


cash_journal_table = Table(
    "cash_journal",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("date", Date, nullable=False),
    Column(
        "operation_type",
        Enum(
            OperationType,
            name="operation_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column(
        "vehicle_id",
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "rental_id",
        UUID(as_uuid=True),
        ForeignKey("rentals.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "expense_category_id",
        UUID(as_uuid=True),
        ForeignKey("expense_categories.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column(
        "payment_method",
        Enum(
            PaymentMethod,
            name="journal_payment_method",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("amount", Numeric(12, 2), nullable=False),
    Column("description", Text, nullable=True),
    Column("receipt_url", String(500), nullable=True),
    Column(
        "confirmed_by",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("confirmed_at", DateTime(timezone=True), nullable=True),
    Column(
        "created_by",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_cash_journal_table() -> None:
    mapper_registry.map_imperatively(
        CashJournalEntry,
        cash_journal_table,
        properties={
            "id_": cash_journal_table.c.id,
            "organization_id": cash_journal_table.c.organization_id,
            "date": cash_journal_table.c.date,
            "operation_type": cash_journal_table.c.operation_type,
            "vehicle_id": cash_journal_table.c.vehicle_id,
            "rental_id": cash_journal_table.c.rental_id,
            "expense_category_id": cash_journal_table.c.expense_category_id,
            "payment_method": cash_journal_table.c.payment_method,
            "amount": cash_journal_table.c.amount,
            "description": cash_journal_table.c.description,
            "receipt_url": cash_journal_table.c.receipt_url,
            "confirmed_by": cash_journal_table.c.confirmed_by,
            "confirmed_at": cash_journal_table.c.confirmed_at,
            "created_by": cash_journal_table.c.created_by,
            "_created_at": composite(UtcDatetime, cash_journal_table.c.created_at),
        },
        column_prefix="__",
    )
