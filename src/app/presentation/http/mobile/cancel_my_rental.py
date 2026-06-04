from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel

from app.core.commands.cancel_own_rental import CancelOwnRental, CancelOwnRentalRequest
from app.core.commands.exceptions import ClientNotFoundError, InvalidRentalStatusTransitionError, RentalNotFoundError
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info


class CancelMyRentalBody(BaseModel):
    reason: str | None = None


def make_cancel_my_rental_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/rentals/{rental_id}/cancel",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidRentalStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def cancel_my_rental(
        rental_id: UUID,
        body: CancelMyRentalBody,
        interactor: FromDishka[CancelOwnRental],
    ) -> None:
        await interactor.execute(
            CancelOwnRentalRequest(
                rental_id=rental_id,
                reason=body.reason,
            )
        )

    return router
