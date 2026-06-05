import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import ClientNotFoundError, InvalidRentalStatusTransitionError, RentalNotFoundError
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import ClientId, RentalId, RentalStatus
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

CANCELLABLE_STATUSES = {RentalStatus.PENDING, RentalStatus.CONFIRMED}


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelOwnRentalRequest:
    rental_id: UUID
    reason: str | None = None


class CancelOwnRental:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        rental_tx_storage: RentalTxStorage,
        client_tx_storage: ClientTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._rental_tx_storage = rental_tx_storage
        self._client_tx_storage = client_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: CancelOwnRentalRequest) -> None:
        logger.info("Cancel own rental: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.rental",
            ),
        )

        client = await self._client_tx_storage.get_by_id(ClientId(current_user.client_id))
        if client is None:
            raise ClientNotFoundError

        rental_id = RentalId(request.rental_id)
        rental = await self._rental_tx_storage.get_by_id(rental_id, for_update=True)
        if rental is None:
            raise RentalNotFoundError

        if rental.client_id != client.id_:
            raise RentalNotFoundError

        if rental.status not in CANCELLABLE_STATUSES:
            raise InvalidRentalStatusTransitionError(f"Cannot cancel rental with status '{rental.status}'.")

        rental.status = RentalStatus.CANCELLED
        rental.cancellation_reason = request.reason
        rental.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Cancel own rental: done.")
