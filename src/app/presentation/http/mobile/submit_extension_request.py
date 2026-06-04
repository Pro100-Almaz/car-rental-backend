from datetime import datetime
from decimal import Decimal
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel

from app.core.commands.exceptions import (
    ClientNotFoundError,
    InvalidRentalStatusTransitionError,
    PendingExtensionExistsError,
    RentalDateOverlapError,
    RentalNotFoundError,
)
from app.core.commands.submit_extension_request import (
    InvalidExtensionDatesError,
    SubmitExtensionRequestCommand,
    SubmitExtensionRequestInput,
    SubmitExtensionRequestResponse,
)
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class SubmitExtensionRequestBody(BaseModel):
    new_end_date: datetime
    additional_cost: Decimal


def make_submit_extension_request_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/rentals/{rental_id}/extend-request",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
            RentalNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidExtensionDatesError: status.HTTP_422_UNPROCESSABLE_CONTENT,
            InvalidRentalStatusTransitionError: status.HTTP_409_CONFLICT,
            PendingExtensionExistsError: status.HTTP_409_CONFLICT,
            RentalDateOverlapError: status.HTTP_409_CONFLICT,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def submit_extension_request(
        rental_id: UUID,
        body: SubmitExtensionRequestBody,
        interactor: FromDishka[SubmitExtensionRequestCommand],
    ) -> SubmitExtensionRequestResponse:
        return await interactor.execute(
            SubmitExtensionRequestInput(
                rental_id=rental_id,
                new_end_date=body.new_end_date,
                additional_cost=body.additional_cost,
            )
        )

    return router
