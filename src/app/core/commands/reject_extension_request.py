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
from app.core.common.entities.types_ import ExtensionRequestId, ExtensionRequestStatus, NotificationType, UserId
from app.core.common.services.notification_service import NotificationService
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class RejectExtensionRequestInput:
    extension_request_id: UUID
    rejection_reason: str


class RejectExtensionRequest:
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

    async def execute(self, request: RejectExtensionRequestInput) -> None:
        logger.info("Reject extension request: started.")

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
            raise InvalidExtensionRequestStatusError(f"Cannot reject extension request with status '{ext_req.status}'.")

        now = UtcDatetime(self._utc_timer.now.value)
        ext_req.status = ExtensionRequestStatus.REJECTED
        ext_req.rejection_reason = request.rejection_reason
        ext_req.reviewed_by = UserId(current_user.id_)
        ext_req.reviewed_at = now.value
        await self._transaction_manager.commit()

        rental = await self._rental_tx_storage.get_by_id(ext_req.rental_id)

        client_id = ext_req.client_id
        org_id = ext_req.organization_id
        if rental is not None:
            client_id = rental.client_id
            org_id = rental.organization_id

        await self._notification_service.send_to_client(
            client_id=client_id,
            organization_id=org_id,
            type_=NotificationType.EXTENSION_REJECTED,
            title="Extension Rejected",
            body=f"Your rental extension request was rejected. Reason: {request.rejection_reason}",
            deep_link=f"/rentals/{ext_req.rental_id}",
            metadata={"rental_id": str(ext_req.rental_id), "extension_request_id": str(ext_req.id_)},
        )

        logger.info("Reject extension request: done.")
