from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.confirm_client_payment import ConfirmClientPayment, ConfirmClientPaymentRequest
from app.core.commands.exceptions import InvalidTransactionStatusTransitionError, TransactionNotFoundError
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info


def make_confirm_payment_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/transactions/{transaction_id}/confirm",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            TransactionNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidTransactionStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def confirm_payment(
        transaction_id: UUID,
        interactor: FromDishka[ConfirmClientPayment],
    ) -> None:
        await interactor.execute(ConfirmClientPaymentRequest(transaction_id=transaction_id))

    return router
