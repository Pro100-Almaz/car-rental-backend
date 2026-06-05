from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.get_my_rental import GetMyRental, GetMyRentalRequest
from app.core.queries.models.mobile_rental import MobileRentalQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_my_rental_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/rentals/{rental_id}",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "Rental not found"}},
    )
    @inject
    async def get_my_rental(
        rental_id: UUID,
        interactor: FromDishka[GetMyRental],
    ) -> MobileRentalQm:
        result = await interactor.execute(GetMyRentalRequest(rental_id=rental_id))
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rental not found.",
            )
        return result

    return router
