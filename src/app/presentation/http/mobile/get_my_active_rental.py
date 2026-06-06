from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import RentalNotFoundError
from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.get_my_active_rental import GetMyActiveRental
from app.core.queries.models.mobile_rental import MobileRentalQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_my_active_rental_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/rentals/active",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "No active rental found"}},
    )
    @inject
    async def get_my_active_rental(
        interactor: FromDishka[GetMyActiveRental],
    ) -> MobileRentalQm:
        result = await interactor.execute()
        if result is None:
            raise RentalNotFoundError
        return result

    return router
