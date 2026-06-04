import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import ExtensionRequestNotFoundError, InvalidExtensionRequestStatusError
from app.core.commands.ports.extension_request_tx_storage import ExtensionRequestTxStorage
from app.core.commands.ports.rental_tx_storage import RentalTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import (
    ExtensionRequestId,
    ExtensionRequestStatus,
    NotificationType,
    RentalId,
    UserId,
)
from app.core.common.services.notification_service import NotificationService
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ApproveExtensionRequestInput:
    extension_request_id: UUID


class ApproveExtensionRequest:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        extension_request_tx_storage: ExtensionRequestTxStorage,
        rental_tx_storage: RentalTxStorage,
        transaction_manager: TransactionManager,
        notification_service: NotificationService,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._extension_request_tx_storage = extension_request_tx_storage
        self._rental_tx_storage = rental_tx_storage
        self._transaction_manager = transaction_manager
        self._notification_service = notification_service

    async def execute(self, request: ApproveExtensionRequestInput) -> None:
        logger.info("Approve extension request: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="rental.update",
            ),
        )

        ext_id = ExtensionRequestId(request.extension_request_id)
        ext_req = await self._extension_request_tx_storage.get_by_id(ext_id, for_update=True)
        if ext_req is None:
            raise ExtensionRequestNotFoundError

        if ext_req.status != ExtensionRequestStatus.PENDING:
            raise InvalidExtensionRequestStatusError(
                f"Cannot approve extension request with status '{ext_req.status}'."
            )

        rental = await self._rental_tx_storage.get_by_id(RentalId(ext_req.rental_id), for_update=True)
        if rental is None:
            raise ExtensionRequestNotFoundError

        now = UtcDatetime(self._utc_timer.now.value)
        ext_req.status = ExtensionRequestStatus.APPROVED
        ext_req.reviewed_by = UserId(current_user.id_)
        ext_req.reviewed_at = now

        rental.scheduled_end = ext_req.new_end_date.value
        rental.estimated_total = rental.estimated_total + ext_req.additional_cost
        rental.updated_at = now
        await self._transaction_manager.commit()

        await self._notification_service.send(
            user_id=rental.client_id,
            organization_id=rental.organization_id,
            type_=NotificationType.EXTENSION_APPROVED,
            title="Extension Approved",
            body=f"Your rental extension has been approved. New end date: {ext_req.new_end_date.value:%Y-%m-%d %H:%M}.",
            deep_link=f"/rentals/{rental.id_}",
            metadata={"rental_id": str(rental.id_), "extension_request_id": str(ext_req.id_)},
        )

        logger.info("Approve extension request: done.")
