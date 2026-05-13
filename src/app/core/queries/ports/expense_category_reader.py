from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.expense_category import ExpenseCategoryQm


class ListExpenseCategoriesQm(TypedDict):
    expense_categories: list[ExpenseCategoryQm]
    total: int


class ExpenseCategoryReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        expense_category_id: UUID,
    ) -> ExpenseCategoryQm | None: ...

    @abstractmethod
    async def list_expense_categories(
        self,
        *,
        organization_id: UUID,
        is_active: bool | None = None,
    ) -> ListExpenseCategoriesQm: ...
