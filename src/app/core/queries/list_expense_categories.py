import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.expense_category_reader import ExpenseCategoryReader, ListExpenseCategoriesQm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListExpenseCategoriesRequest:
    organization_id: UUID
    is_active: bool | None = None


class ListExpenseCategories:
    def __init__(
        self,
        expense_category_reader: ExpenseCategoryReader,
    ) -> None:
        self._expense_category_reader = expense_category_reader

    async def execute(self, request: ListExpenseCategoriesRequest) -> ListExpenseCategoriesQm:
        logger.info("List expense categories: started.")

        result = await self._expense_category_reader.list_expense_categories(
            organization_id=request.organization_id,
            is_active=request.is_active,
        )

        logger.info("List expense categories: done.")
        return result
