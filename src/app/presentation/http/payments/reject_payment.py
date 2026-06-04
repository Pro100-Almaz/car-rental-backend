from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel

from app.core.commands.exceptions import InvalidTransactionStatusTransitionError, TransactionNotFoundError
from app.core.commands.reject_client_payment import RejectClientPayment, RejectClientPaymentRequest
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info


class RejectPaymentBody(BaseModel):
    rejection_reason: str


def make_reject_payment_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/transactions/{transaction_id}/reject",
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
    async def reject_payment(
        transaction_id: UUID,
        body: RejectPaymentBody,
        interactor: FromDishka[RejectClientPayment],
    ) -> None:
        await interactor.execute(
            RejectClientPaymentRequest(
                transaction_id=transaction_id,
                rejection_reason=body.rejection_reason,
            )
        )

    return router
