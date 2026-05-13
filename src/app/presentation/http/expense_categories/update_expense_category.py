from typing import Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import ExpenseCategoryNotFoundError
from app.core.commands.update_expense_category import UpdateExpenseCategory, UpdateExpenseCategoryRequest
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class UpdateExpenseCategoryBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str | None = None
    type_: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


def make_update_expense_category_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{expense_category_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            ExpenseCategoryNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def update_expense_category(
        expense_category_id: UUID,
        body: UpdateExpenseCategoryBody,
        interactor: FromDishka[UpdateExpenseCategory],
    ) -> None:
        kwargs: dict[str, Any] = {"expense_category_id": expense_category_id}
        for field_name in body.model_fields_set:
            kwargs[field_name] = getattr(body, field_name)
        request = UpdateExpenseCategoryRequest(**kwargs)
        await interactor.execute(request)

    return router
