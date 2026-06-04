from decimal import Decimal
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel

from app.core.commands.exceptions import ClientNotFoundError
from app.core.commands.record_client_payment import (
    InvalidPaymentAmountError,
    RecordClientPayment,
    RecordClientPaymentRequest,
    RecordClientPaymentResponse,
)
from app.core.common.authorization.exceptions import AuthorizationError
from app.core.common.entities.types_ import PaymentMethod, TransactionType
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info


class RecordPaymentBody(BaseModel):
    organization_id: UUID
    rental_id: UUID | None = None
    type: TransactionType
    amount: Decimal
    payment_method: PaymentMethod
    client_note: str | None = None


def make_record_payment_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/payments/record",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            InvalidPaymentAmountError: status.HTTP_422_UNPROCESSABLE_CONTENT,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def record_payment(
        body: RecordPaymentBody,
        interactor: FromDishka[RecordClientPayment],
    ) -> RecordClientPaymentResponse:
        return await interactor.execute(
            RecordClientPaymentRequest(
                organization_id=body.organization_id,
                rental_id=body.rental_id,
                type=body.type,
                amount=body.amount,
                payment_method=body.payment_method,
                client_note=body.client_note,
            )
        )

    return router
