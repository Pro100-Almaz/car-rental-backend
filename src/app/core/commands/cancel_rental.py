import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import InvalidRentalStatusTransitionError, RentalNotFoundError
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.commands.rental_transitions import VALID_RENTAL_TRANSITIONS
from app.core.common.audit_log import emit as audit_emit
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import NotificationType, RentalId, RentalStatus
from app.core.common.services.notification_service import NotificationService
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelRentalRequest:
    rental_id: UUID
    reason: str | None = None


class CancelRental:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        rental_tx_storage: RentalTxStorage,
        transaction_manager: TransactionManager,
        notification_service: NotificationService,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._rental_tx_storage = rental_tx_storage
        self._transaction_manager = transaction_manager
        self._notification_service = notification_service

    async def execute(self, request: CancelRentalRequest) -> None:
        logger.info("Cancel rental: started.")

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

        allowed = VALID_RENTAL_TRANSITIONS.get(rental.status, set())
        if RentalStatus.CANCELLED not in allowed:
            raise InvalidRentalStatusTransitionError(f"Cannot cancel rental with status '{rental.status}'.")

        previous_status = rental.status
        rental.status = RentalStatus.CANCELLED
        rental.cancellation_reason = request.reason
        rental.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        audit_emit(
            "rental.cancelled",
            rental_id=str(rental.id_),
            manager_id=str(current_user.id_),
            client_id=str(rental.client_id),
            vehicle_id=str(rental.vehicle_id),
            previous_status=str(previous_status),
        )

        # Only notify client if the admin cancelled — not if already user-cancelled.
        if previous_status != RentalStatus.CANCELLED:
            try:
                await self._notification_service.send_to_client(
                    client_id=rental.client_id,
                    organization_id=rental.organization_id,
                    type_=NotificationType.BOOKING_CANCELLED,
                    title="Rental Cancelled",
                    body="Your rental has been cancelled by the manager.",
                    deep_link=f"/rentals/{rental.id_}",
                    metadata={"rental_id": str(rental.id_)},
                )
            except Exception:
                logger.warning(
                    "Failed to send RENTAL_CANCELLED notification for rental %s; ignoring.",
                    rental.id_,
                    exc_info=True,
                )

        logger.info("Cancel rental: done.")
