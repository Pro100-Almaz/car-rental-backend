from typing import Protocol

from app.core.common.entities.expense_category import ExpenseCategory
from app.core.common.entities.types_ import ExpenseCategoryId


class ExpenseCategoryTxStorage(Protocol):
    def add(self, expense_category: ExpenseCategory) -> None: ...

    async def get_by_id(
        self,
        expense_category_id: ExpenseCategoryId,
        *,
        for_update: bool = False,
    ) -> ExpenseCategory | None: ...
