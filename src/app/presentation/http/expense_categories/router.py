from fastapi import APIRouter

from app.presentation.http.expense_categories.create_expense_category import make_create_expense_category_router
from app.presentation.http.expense_categories.list_expense_categories import make_list_expense_categories_router
from app.presentation.http.expense_categories.update_expense_category import make_update_expense_category_router


def make_expense_categories_router() -> APIRouter:
    router = APIRouter(
        prefix="/expense-categories",
        tags=["Expense Categories"],
    )
    router.include_router(make_create_expense_category_router())
    router.include_router(make_list_expense_categories_router())
    router.include_router(make_update_expense_category_router())
    return router
