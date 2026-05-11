import logging
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.core.commands.exceptions import InvalidRentalStatusTransitionError, RentalNotFoundError
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import RentalId, RentalStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CompleteRentalRequest:
    rental_id: UUID
    actual_total: Decimal
    late_fee: Decimal = Decimal(0)
    mileage_surcharge: Decimal = Decimal(0)
    fuel_charge: Decimal = Decimal(0)
    wash_fee: Decimal = Decimal(0)
    damage_charge: Decimal = Decimal(0)
    fine_charge: Decimal = Decimal(0)
    deposit_refund_amount: Decimal = Decimal(0)


class CompleteRental:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        rental_tx_storage: RentalTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._rental_tx_storage = rental_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: CompleteRentalRequest) -> None:
        logger.info("Complete rental: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="rental.update",
            ),
        )

        rental_id = RentalId(request.rental_id)
        rental = await self._rental_tx_storage.get_by_id(rental_id, for_update=True)
        if rental is None:
            raise RentalNotFoundError

        if rental.status != RentalStatus.RETURNING:
            raise InvalidRentalStatusTransitionError(f"Complete requires status 'returning', got '{rental.status}'.")

        now = self._utc_timer.now.value
        rental.status = RentalStatus.COMPLETED
        rental.actual_total = request.actual_total
        rental.late_fee = request.late_fee
        rental.mileage_surcharge = request.mileage_surcharge
        rental.fuel_charge = request.fuel_charge
        rental.wash_fee = request.wash_fee
        rental.damage_charge = request.damage_charge
        rental.fine_charge = request.fine_charge
        rental.deposit_refund_amount = request.deposit_refund_amount
        if rental.actual_end is None:
            rental.actual_end = now
        rental.updated_at = UtcDatetime(now)
        await self._transaction_manager.commit()

        logger.info("Complete rental: done.")
