from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.list_booking_requests import ListBookingRequests, ListBookingRequestsRequest
from app.core.queries.ports.rental_reader import ListRentalsQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_booking_requests_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/booking-requests",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_booking_requests(
        interactor: FromDishka[ListBookingRequests],
        organization_id: UUID = Query(...),
    ) -> ListRentalsQm:
        return await interactor.execute(
            ListBookingRequestsRequest(organization_id=organization_id)
        )

    return router
