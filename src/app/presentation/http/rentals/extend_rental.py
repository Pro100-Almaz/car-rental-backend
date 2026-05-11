from datetime import datetime
from decimal import Decimal
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import InvalidRentalStatusTransitionError, RentalNotFoundError
from app.core.commands.extend_rental import ExtendRental, ExtendRentalRequest
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ExtendRentalBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    new_scheduled_end: datetime
    new_estimated_total: Decimal


def make_extend_rental_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{rental_id}/extend",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidRentalStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def extend_rental(
        rental_id: UUID,
        body: ExtendRentalBody,
        interactor: FromDishka[ExtendRental],
    ) -> None:
        request = ExtendRentalRequest(
            rental_id=rental_id,
            new_scheduled_end=body.new_scheduled_end,
            new_estimated_total=body.new_estimated_total,
        )
        await interactor.execute(request)

    return router
