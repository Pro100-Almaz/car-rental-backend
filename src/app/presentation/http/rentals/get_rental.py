from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import RentalNotFoundError
from app.core.queries.get_rental import GetRental, GetRentalRequest
from app.core.queries.models.rental import RentalQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_rental_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{rental_id}",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "Rental not found"}},
    )
    @inject
    async def get_rental(
        rental_id: UUID,
        interactor: FromDishka[GetRental],
    ) -> RentalQm:
        result = await interactor.execute(GetRentalRequest(rental_id=rental_id))
        if result is None:
            raise RentalNotFoundError
        return result

    return router
