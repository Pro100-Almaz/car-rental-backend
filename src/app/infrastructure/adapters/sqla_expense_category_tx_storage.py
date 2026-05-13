from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.expense_category_tx_storage import ExpenseCategoryTxStorage
from app.core.common.entities.expense_category import ExpenseCategory
from app.core.common.entities.types_ import ExpenseCategoryId
from app.infrastructure.exceptions import StorageError


class SqlaExpenseCategoryTxStorage(ExpenseCategoryTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, expense_category: ExpenseCategory) -> None:
        try:
            self._session.add(expense_category)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        expense_category_id: ExpenseCategoryId,
        *,
        for_update: bool = False,
    ) -> ExpenseCategory | None:
        try:
            return await self._session.get(
                ExpenseCategory,
                expense_category_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
