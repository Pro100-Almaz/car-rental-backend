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
from app.core.common.entities.types_ import DepositType, PrepaymentStatus, RentalId, RentalStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

_UNSET = object()

_EDITABLE_STATUSES = {RentalStatus.PENDING, RentalStatus.CONFIRMED}


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateRentalRequest:
    rental_id: UUID
    scheduled_start: datetime | object = _UNSET
    scheduled_end: datetime | object = _UNSET
    base_rate: Decimal | object = _UNSET
    estimated_total: Decimal | object = _UNSET
    discount_code: str | None | object = _UNSET
    discount_amount: Decimal | object = _UNSET
    deposit_type: DepositType | object = _UNSET
    deposit_amount: Decimal | object = _UNSET
    prepayment_amount: Decimal | object = _UNSET
    prepayment_status: PrepaymentStatus | object = _UNSET
    notes: str | None | object = _UNSET


class UpdateRental:
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

    async def execute(self, request: UpdateRentalRequest) -> None:
        logger.info("Update rental: started.")

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

        if rental.status not in _EDITABLE_STATUSES:
            raise InvalidRentalStatusTransitionError(
                f"Cannot edit rental with status '{rental.status}'. Only pending/confirmed rentals can be edited."
            )

        changed = False
        for attr in (
            "scheduled_start",
            "scheduled_end",
            "base_rate",
            "estimated_total",
            "discount_code",
            "discount_amount",
            "deposit_type",
            "deposit_amount",
            "prepayment_amount",
            "prepayment_status",
            "notes",
        ):
            val = getattr(request, attr)
            if val is not _UNSET and val != getattr(rental, attr):
                setattr(rental, attr, val)
                changed = True

        if changed:
            rental.updated_at = UtcDatetime(self._utc_timer.now.value)
            await self._transaction_manager.commit()

        logger.info("Update rental: done.")
