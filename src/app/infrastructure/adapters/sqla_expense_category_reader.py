from typing import Any
from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.expense_category import ExpenseCategoryQm
from app.core.queries.ports.expense_category_reader import ExpenseCategoryReader, ListExpenseCategoriesQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.expense_category import expense_categories_table


class SqlaExpenseCategoryReader(ExpenseCategoryReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_columns(self) -> tuple[Any, ...]:
        return (
            expense_categories_table.c.id,
            expense_categories_table.c.organization_id,
            expense_categories_table.c.name,
            expense_categories_table.c.type.label("type_"),
            expense_categories_table.c.is_system,
            expense_categories_table.c.sort_order,
            expense_categories_table.c.is_active,
            expense_categories_table.c.created_at,
        )

    def _row_to_qm(self, row: Row[Any]) -> ExpenseCategoryQm:
        return ExpenseCategoryQm(
            id=row.id,
            organization_id=row.organization_id,
            name=row.name,
            type_=row.type_,
            is_system=row.is_system,
            sort_order=row.sort_order,
            is_active=row.is_active,
            created_at=row.created_at,
        )

    async def get_by_id(
        self,
        *,
        expense_category_id: UUID,
    ) -> ExpenseCategoryQm | None:
        stmt = select(*self._base_columns()).where(
            expense_categories_table.c.id == expense_category_id,
        )
        try:
            result = await self._session.execute(stmt)
            row = result.one_or_none()
        except SQLAlchemyError as e:
            raise ReaderError from e
        if row is None:
            return None
        return self._row_to_qm(row)

    async def list_expense_categories(
        self,
        *,
        organization_id: UUID,
        is_active: bool | None = None,
    ) -> ListExpenseCategoriesQm:
        stmt = (
            select(*self._base_columns())
            .where(expense_categories_table.c.organization_id == organization_id)
            .order_by(expense_categories_table.c.sort_order.asc())
        )
        if is_active is not None:
            stmt = stmt.where(expense_categories_table.c.is_active == is_active)
        try:
            result = await self._session.execute(stmt)
            rows = result.all()
        except SQLAlchemyError as e:
            raise ReaderError from e
        expense_categories = [self._row_to_qm(row) for row in rows]
        return ListExpenseCategoriesQm(
            expense_categories=expense_categories,
            total=len(expense_categories),
        )
