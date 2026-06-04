from typing import Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import InvalidRentalStatusTransitionError, RentalNotFoundError
from app.core.commands.update_rental import UpdateRental, UpdateRentalRequest
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class UpdateRentalBody(BaseModel):
    model_config = ConfigDict(frozen=True)
    scheduled_start: str | None = None
    scheduled_end: str | None = None
    base_rate: float | None = None
    estimated_total: float | None = None
    discount_code: str | None = None
    discount_amount: float | None = None
    deposit_type: str | None = None
    deposit_amount: float | None = None
    prepayment_amount: float | None = None
    prepayment_status: str | None = None
    notes: str | None = None


def make_update_rental_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{rental_id}",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidRentalStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def update_rental(
        rental_id: UUID,
        body: UpdateRentalBody,
        interactor: FromDishka[UpdateRental],
    ) -> None:
        fields_set = body.model_fields_set
        kwargs: dict[str, Any] = {"rental_id": rental_id}
        for field_name in UpdateRentalBody.model_fields:
            if field_name in fields_set:
                kwargs[field_name] = getattr(body, field_name)
        request = UpdateRentalRequest(**kwargs)
        await interactor.execute(request)

    return router
