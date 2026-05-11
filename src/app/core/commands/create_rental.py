import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.rental import Rental
from app.core.common.entities.types_ import (
    BookingType,
    ClientId,
    DepositStatus,
    DepositType,
    OrganizationId,
    PrepaymentStatus,
    RateType,
    RentalStatus,
    UserId,
    VehicleId,
)
from app.core.common.factories.id_factory import create_rental_id
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRentalRequest:
    organization_id: UUID
    vehicle_id: UUID
    client_id: UUID
    manager_id: UUID | None = None
    booking_type: BookingType
    scheduled_start: datetime
    scheduled_end: datetime
    base_rate: Decimal
    rate_type: RateType
    estimated_total: Decimal
    discount_code: str | None = None
    discount_amount: Decimal = Decimal(0)
    deposit_type: DepositType
    deposit_amount: Decimal
    prepayment_amount: Decimal = Decimal(0)
    prepayment_status: PrepaymentStatus = PrepaymentStatus.NONE
    notes: str | None = None


class CreateRentalResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateRental:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        rental_tx_storage: RentalTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._rental_tx_storage = rental_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateRentalRequest) -> CreateRentalResponse:
        logger.info("Create rental: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="rental.create",
            ),
        )

        now = UtcDatetime(self._utc_timer.now.value)
        rental = Rental(
            id_=create_rental_id(),
            organization_id=OrganizationId(request.organization_id),
            vehicle_id=VehicleId(request.vehicle_id),
            client_id=ClientId(request.client_id),
            manager_id=UserId(request.manager_id) if request.manager_id else None,
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
            notes=request.notes,
            created_at=now,
            updated_at=now,
        )
        self._rental_tx_storage.add(rental)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Create rental: done.")
        return CreateRentalResponse(
            id=rental.id_,
            created_at=rental.created_at.value,
        )
