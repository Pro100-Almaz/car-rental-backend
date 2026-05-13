from enum import StrEnum

from sqlalchemy import UUID, Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Table
from sqlalchemy.orm import composite

from app.core.common.entities.expense_category import ExpenseCategory
from app.core.common.entities.types_ import ExpenseCategoryType
from app.core.common.value_objects.utc_datetime import UtcDatetime
from app.infrastructure.persistence_sqla.registry import mapper_registry


def get_strenum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [e.value for e in enum_cls]


expense_categories_table = Table(
    "expense_categories",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("name", String(200), nullable=False),
    Column(
        "type",
        Enum(
            ExpenseCategoryType,
            name="expense_category_type",
            native_enum=False,
            validate_strings=True,
            values_callable=get_strenum_values,
        ),
        nullable=False,
    ),
    Column("is_system", Boolean, nullable=False, default=False),
    Column("sort_order", Integer, nullable=False, default=0),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def map_expense_categories_table() -> None:
    mapper_registry.map_imperatively(
        ExpenseCategory,
        expense_categories_table,
        properties={
            "id_": expense_categories_table.c.id,
            "organization_id": expense_categories_table.c.organization_id,
            "name": expense_categories_table.c.name,
            "type_": expense_categories_table.c.type,
            "is_system": expense_categories_table.c.is_system,
            "sort_order": expense_categories_table.c.sort_order,
            "is_active": expense_categories_table.c.is_active,
            "_created_at": composite(UtcDatetime, expense_categories_table.c.created_at),
        },
        column_prefix="__",
    )
