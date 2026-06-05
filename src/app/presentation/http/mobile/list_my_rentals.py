from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.list_my_rentals import ListMyRentals, ListMyRentalsRequest
from app.core.queries.ports.mobile_rental_reader import ListMobileRentalsQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_my_rentals_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/rentals",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_my_rentals(
        interactor: FromDishka[ListMyRentals],
        rental_status: str | None = Query(None, alias="status"),
    ) -> ListMobileRentalsQm:
        return await interactor.execute(ListMyRentalsRequest(status=rental_status))

    return router
