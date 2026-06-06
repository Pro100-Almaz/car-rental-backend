import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.exceptions import (
    ClientNotFoundError,
    RentalDateOverlapError,
    VehicleNotFoundError,
)
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.ports.vehicle_tx_storage import VehicleTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.rental import Rental
from app.core.common.entities.types_ import (
    BookingType,
    DepositStatus,
    DepositType,
    OrganizationId,
    PrepaymentStatus,
    RateType,
    RentalSource,
    RentalStatus,
    VehicleId,
    VehicleStatus,
)
from typing import ClassVar

from app.core.common.exceptions import BaseError
from app.core.common.factories.id_factory import create_rental_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

MAX_BOOKING_DAYS = 30
MAX_PICKUP_NOTES_LEN = 500


class ClientNotVerifiedError(BaseError):
    default_message: ClassVar[str] = "Client must be verified before booking."


class ClientBlacklistedError(BaseError):
    default_message: ClassVar[str] = "Blacklisted clients cannot create bookings."


class VehicleNotAvailableError(BaseError):
    default_message: ClassVar[str] = "Vehicle is not available for booking."


class InvalidBookingDatesError(BaseError):
    default_message: ClassVar[str] = "Invalid booking dates."


@dataclass(frozen=True, slots=True, kw_only=True)
class SubmitBookingRequest:
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


class SubmitBookingResponse(TypedDict):
    id: UUID
    created_at: datetime


class SubmitBookingRequestCommand:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        rental_tx_storage: RentalTxStorage,
        client_tx_storage: ClientTxStorage,
        vehicle_tx_storage: VehicleTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._rental_tx_storage = rental_tx_storage
        self._client_tx_storage = client_tx_storage
        self._vehicle_tx_storage = vehicle_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    def _validate_request(self, request: SubmitBookingRequest) -> None:
        now_dt = self._utc_timer.now.value
        if request.scheduled_start <= now_dt:
            raise InvalidBookingDatesError("Scheduled start must be in the future.")
        if request.scheduled_end <= request.scheduled_start:
            raise InvalidBookingDatesError("Scheduled end must be after start.")
        duration = request.scheduled_end - request.scheduled_start
        if duration.days > MAX_BOOKING_DAYS:
            raise InvalidBookingDatesError(f"Booking duration cannot exceed {MAX_BOOKING_DAYS} days.")
        if request.pickup_notes and len(request.pickup_notes) > MAX_PICKUP_NOTES_LEN:
            raise InvalidBookingDatesError(f"Pickup notes cannot exceed {MAX_PICKUP_NOTES_LEN} characters.")

    async def execute(self, request: SubmitBookingRequest) -> SubmitBookingResponse:
        logger.info("Submit booking request: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.rental",
            ),
        )

        self._validate_request(request)

        client = await self._client_tx_storage.get_by_user_id(current_user.id_)
        if client is None:
            raise ClientNotFoundError

        if client.verification_status != "verified":
            raise ClientNotVerifiedError
        if client.is_blacklisted:
            raise ClientBlacklistedError

        vehicle = await self._vehicle_tx_storage.get_by_id(VehicleId(request.vehicle_id))
        if vehicle is None:
            raise VehicleNotFoundError
        if vehicle.status != VehicleStatus.AVAILABLE:
            raise VehicleNotAvailableError

        has_overlap = await self._rental_tx_storage.has_overlap(
            vehicle_id=VehicleId(request.vehicle_id),
            scheduled_start=request.scheduled_start,
            scheduled_end=request.scheduled_end,
        )
        if has_overlap:
            raise RentalDateOverlapError

        now = UtcDatetime(self._utc_timer.now.value)
        rental = Rental(
            id_=create_rental_id(),
            organization_id=OrganizationId(request.organization_id),
            vehicle_id=VehicleId(request.vehicle_id),
            client_id=client.id_,
            manager_id=None,
            status=RentalStatus.PENDING,
            booking_type=request.booking_type,
            booked_at=self._utc_timer.now.value,
            scheduled_start=request.scheduled_start,
            scheduled_end=request.scheduled_end,
            actual_start=None,
            actual_end=None,
            base_rate=request.base_rate,
            rate_type=request.rate_type,
            estimated_total=request.estimated_total,
            actual_total=None,
            discount_code=request.discount_code,
            discount_amount=request.discount_amount,
            late_fee=Decimal(0),
            mileage_surcharge=Decimal(0),
            fuel_charge=Decimal(0),
            wash_fee=Decimal(0),
            damage_charge=Decimal(0),
            fine_charge=Decimal(0),
            deposit_type=request.deposit_type,
            deposit_amount=request.deposit_amount,
            deposit_status=DepositStatus.PENDING,
            deposit_refund_amount=Decimal(0),
            checkin_data=None,
            checkout_data=None,
            invoice_url=None,
            cancellation_reason=None,
            prepayment_amount=request.prepayment_amount,
            prepayment_status=request.prepayment_status,
            source=RentalSource.MOBILE,
            pickup_notes=request.pickup_notes,
            notes=None,
            created_at=now,
            updated_at=now,
        )
        self._rental_tx_storage.add(rental)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Submit booking request: done.")
        return SubmitBookingResponse(
            id=rental.id_,
            created_at=rental.created_at.value,
        )
