from typing import Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import InvestorNotFoundError
from app.core.commands.update_investor import UpdateInvestor, UpdateInvestorRequest
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class UpdateInvestorBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    full_name: str | None = None
    type_: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    user_id: UUID | None = None
    notes: str | None = None


def make_update_investor_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{investor_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
            InvestorNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def update_investor(
        investor_id: UUID,
        body: UpdateInvestorBody,
        interactor: FromDishka[UpdateInvestor],
    ) -> None:
        kwargs: dict[str, Any] = {"investor_id": investor_id}
        for field_name in body.model_fields_set:
            kwargs[field_name] = getattr(body, field_name)
        request = UpdateInvestorRequest(**kwargs)
        await interactor.execute(request)

    return router
