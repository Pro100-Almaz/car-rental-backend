from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import InvalidRentalStatusTransitionError, RentalNotFoundError
from app.core.commands.transition_rental import TransitionRental, TransitionRentalRequest
from app.core.common.authorization.exceptions import AuthorizationError
from app.core.common.entities.types_ import RentalStatus
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class TransitionRentalBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: RentalStatus


def make_transition_rental_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{rental_id}/transition",
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
    async def transition_rental(
        rental_id: UUID,
        body: TransitionRentalBody,
        interactor: FromDishka[TransitionRental],
    ) -> None:
        request = TransitionRentalRequest(
            rental_id=rental_id,
            status=body.status,
        )
        await interactor.execute(request)

    return router
