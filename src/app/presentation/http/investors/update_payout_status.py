from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import InvalidPayoutStatusTransitionError, InvestorPayoutNotFoundError
from app.core.commands.update_payout_status import UpdatePayoutStatus, UpdatePayoutStatusRequest
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_update_payout_status_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/payouts/{payout_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            InvestorPayoutNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidPayoutStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def update_payout_status(
        payout_id: UUID,
        request: UpdatePayoutStatusRequest,
        interactor: FromDishka[UpdatePayoutStatus],
    ) -> None:
        await interactor.execute(request)

    return router
