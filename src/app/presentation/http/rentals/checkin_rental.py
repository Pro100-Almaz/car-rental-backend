from typing import Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.checkin_rental import CheckinRental, CheckinRentalRequest
from app.core.commands.exceptions import InvalidRentalStatusTransitionError, RentalNotFoundError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class CheckinRentalBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    checkin_data: dict[str, Any]


def make_checkin_rental_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{rental_id}/checkin",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidRentalStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def checkin_rental(
        rental_id: UUID,
        body: CheckinRentalBody,
        interactor: FromDishka[CheckinRental],
    ) -> None:
        request = CheckinRentalRequest(
            rental_id=rental_id,
            checkin_data=body.checkin_data,
        )
        await interactor.execute(request)

    return router
