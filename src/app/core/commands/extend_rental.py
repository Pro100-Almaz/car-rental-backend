import logging
from dataclasses import dataclass
from datetime import datetime
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

_EXTENDABLE_STATUSES = {RentalStatus.CONFIRMED, RentalStatus.ACTIVE}


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtendRentalRequest:
    rental_id: UUID
    new_scheduled_end: datetime
    new_estimated_total: Decimal


class ExtendRental:
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

    async def execute(self, request: ExtendRentalRequest) -> None:
        logger.info("Extend rental: started.")

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

        if rental.status not in _EXTENDABLE_STATUSES:
            raise InvalidRentalStatusTransitionError(f"Cannot extend rental with status '{rental.status}'.")

        rental.scheduled_end = request.new_scheduled_end
        rental.estimated_total = request.new_estimated_total
        rental.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Extend rental: done.")
