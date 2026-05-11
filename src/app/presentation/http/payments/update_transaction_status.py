from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import InvalidTransactionStatusTransitionError, TransactionNotFoundError
from app.core.commands.update_transaction_status import UpdateTransactionStatus, UpdateTransactionStatusRequest
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_update_transaction_status_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/transactions/status",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            TransactionNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidTransactionStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def update_transaction_status(
        request: UpdateTransactionStatusRequest,
        interactor: FromDishka[UpdateTransactionStatus],
    ) -> None:
        await interactor.execute(request)

    return router
