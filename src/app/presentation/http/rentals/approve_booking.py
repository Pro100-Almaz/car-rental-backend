from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, status
from fastapi_error_map import ErrorAwareRouter
from slowapi.errors import RateLimitExceeded

from app.core.commands.approve_booking_request import ApproveBookingRequest, ApproveBookingRequestInput
from app.core.commands.exceptions import RentalDateOverlapError, RentalNotFoundError, RentalNotPendingError
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.infrastructure.rate_limit import get_user_id_or_ip, limiter
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_429_RATE_LIMITED_RULE, HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_approve_booking_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{rental_id}/approve",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
            RentalNotPendingError: status.HTTP_409_CONFLICT,
            RentalDateOverlapError: status.HTTP_409_CONFLICT,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            RateLimitExceeded: HTTP_429_RATE_LIMITED_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @limiter.limit("120/minute", key_func=get_user_id_or_ip)
    @inject
    async def approve_booking(
        rental_id: UUID,
        request: Request,
        interactor: FromDishka[ApproveBookingRequest],
    ) -> None:
        await interactor.execute(ApproveBookingRequestInput(rental_id=rental_id))

    return router
