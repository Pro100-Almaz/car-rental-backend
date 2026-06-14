import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import RentalNotFoundError, RentalNotPendingError
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.audit_log import emit as audit_emit
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import NotificationType, RentalId, RentalStatus, UserId
from app.core.common.services.notification_service import NotificationService
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class RejectBookingRequestInput:
    rental_id: UUID
    rejection_reason: str


class RejectBookingRequest:
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

    async def execute(self, request: RejectBookingRequestInput) -> None:
        logger.info("Reject booking request: started.")

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

        if rental.status != RentalStatus.PENDING:
            raise RentalNotPendingError

        now = UtcDatetime(self._utc_timer.now.value)
        rental.status = RentalStatus.CANCELLED
        rental.rejection_reason = request.rejection_reason
        rental.cancellation_reason = None  # rejection != cancellation
        rental.manager_id = UserId(current_user.id_)
        rental.updated_at = now
        await self._transaction_manager.commit()

        audit_emit(
            "rental.booking.rejected",
            rental_id=str(rental.id_),
            manager_id=str(current_user.id_),
            client_id=str(rental.client_id),
            rejection_reason=request.rejection_reason,
        )

        try:
            await self._notification_service.send_to_client(
                client_id=rental.client_id,
                organization_id=rental.organization_id,
                type_=NotificationType.BOOKING_CANCELLED,
                title="Booking Rejected",
                body=f"Your booking request has been rejected. Reason: {request.rejection_reason}",
                deep_link=f"/rentals/{rental.id_}",
                metadata={
                    "rental_id": str(rental.id_),
                    "rejection_reason": request.rejection_reason,
                },
            )
        except Exception:
            logger.warning(
                "Failed to send RENTAL_REJECTED notification for rental %s; ignoring.",
                rental.id_,
                exc_info=True,
            )

        logger.info("Reject booking request: done.")
