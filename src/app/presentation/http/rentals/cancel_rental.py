from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.cancel_rental import CancelRental, CancelRentalRequest
from app.core.commands.exceptions import InvalidRentalStatusTransitionError, RentalNotFoundError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class CancelRentalBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    reason: str | None = None


def make_cancel_rental_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{rental_id}/cancel",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidRentalStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def cancel_rental(
        rental_id: UUID,
        body: CancelRentalBody,
        interactor: FromDishka[CancelRental],
    ) -> None:
        request = CancelRentalRequest(
            rental_id=rental_id,
            reason=body.reason,
        )
        await interactor.execute(request)

    return router
