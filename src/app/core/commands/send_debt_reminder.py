import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import ClientNotFoundError
from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import ClientId, NotificationType
from app.core.common.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class SendDebtReminderRequest:
    client_id: UUID
    message: str | None = None


class SendDebtReminder:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_tx_storage: ClientTxStorage,
        notification_service: NotificationService,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_tx_storage = client_tx_storage
        self._notification_service = notification_service

    async def execute(self, request: SendDebtReminderRequest) -> None:
        logger.info("Send debt reminder: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="client.edit",
            ),
        )

        client = await self._client_tx_storage.get_by_id(ClientId(request.client_id))
        if client is None:
            raise ClientNotFoundError

        if client.user_id is None:
            raise ClientNotFoundError("Client has no linked user account.")

        body = (
            request.message or "You have an outstanding balance. Please make a payment to continue using our services."
        )

        await self._notification_service.send(
            user_id=client.user_id,
            organization_id=client.organization_id,
            type_=NotificationType.DEBT_REMINDER,
            title="Payment Reminder",
            body=body,
            deep_link="/payments/outstanding",
            metadata={"client_id": str(client.id_)},
        )

        logger.info("Send debt reminder: done.")
