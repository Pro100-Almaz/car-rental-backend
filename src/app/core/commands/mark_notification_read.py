import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.ports.notification_tx_storage import NotificationTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import NotificationId
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


class NotificationNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class MarkNotificationReadRequest:
    notification_id: UUID


class MarkNotificationRead:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        notification_tx_storage: NotificationTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._notification_tx_storage = notification_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: MarkNotificationReadRequest) -> None:
        logger.info("Mark notification read: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.notifications",
            ),
        )

        notification_id = NotificationId(request.notification_id)
        notification = await self._notification_tx_storage.get_by_id(
            notification_id, for_update=True,
        )
        if notification is None:
            raise NotificationNotFoundError

        if notification.user_id != current_user.id_:
            raise NotificationNotFoundError

        if not notification.is_read:
            now = UtcDatetime(self._utc_timer.now.value)
            notification.is_read = True
            notification.read_at = now
            await self._transaction_manager.commit()

        logger.info("Mark notification read: done.")
