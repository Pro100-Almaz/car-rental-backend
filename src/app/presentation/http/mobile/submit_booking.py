from datetime import datetime
from decimal import Decimal
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel

from app.core.commands.exceptions import ClientNotFoundError, RentalDateOverlapError, VehicleNotFoundError
from app.core.commands.submit_booking_request import (
    ClientBlacklistedError,
    ClientNotVerifiedError,
    InvalidBookingDatesError,
    SubmitBookingRequest,
    SubmitBookingRequestCommand,
    SubmitBookingResponse,
    VehicleNotAvailableError,
)
from app.core.common.authorization.exceptions import AuthorizationError
from app.core.common.entities.types_ import BookingType, DepositType, PrepaymentStatus, RateType
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info


class SubmitBookingBody(BaseModel):
    organization_id: UUID
    vehicle_id: UUID
    booking_type: BookingType
    scheduled_start: datetime
    scheduled_end: datetime
    base_rate: Decimal
    rate_type: RateType
    estimated_total: Decimal
    deposit_type: DepositType
    deposit_amount: Decimal
    discount_code: str | None = None
    discount_amount: Decimal = Decimal(0)
    prepayment_amount: Decimal = Decimal(0)
    prepayment_status: PrepaymentStatus = PrepaymentStatus.NONE
    pickup_notes: str | None = None


def make_submit_booking_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/rentals",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            InvalidBookingDatesError: status.HTTP_422_UNPROCESSABLE_CONTENT,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
            ClientNotVerifiedError: status.HTTP_403_FORBIDDEN,
            ClientBlacklistedError: status.HTTP_403_FORBIDDEN,
            VehicleNotFoundError: status.HTTP_404_NOT_FOUND,
            VehicleNotAvailableError: status.HTTP_409_CONFLICT,
            RentalDateOverlapError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def submit_booking(
        body: SubmitBookingBody,
        interactor: FromDishka[SubmitBookingRequestCommand],
    ) -> SubmitBookingResponse:
        return await interactor.execute(
            SubmitBookingRequest(
                organization_id=body.organization_id,
                vehicle_id=body.vehicle_id,
                booking_type=body.booking_type,
                scheduled_start=body.scheduled_start,
                scheduled_end=body.scheduled_end,
                base_rate=body.base_rate,
                rate_type=body.rate_type,
                estimated_total=body.estimated_total,
                deposit_type=body.deposit_type,
                deposit_amount=body.deposit_amount,
                discount_code=body.discount_code,
                discount_amount=body.discount_amount,
                prepayment_amount=body.prepayment_amount,
                prepayment_status=body.prepayment_status,
                pickup_notes=body.pickup_notes,
            )
        )

    return router
