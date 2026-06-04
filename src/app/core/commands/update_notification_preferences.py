import logging
from dataclasses import dataclass
from typing import Any

from app.core.commands.exceptions import UserNotFoundError
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.user_tx_storage import UserTxStorage
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import UserId
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateNotificationPreferencesRequest:
    preferences: dict[str, Any]


class UpdateNotificationPreferences:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        user_tx_storage: UserTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._user_tx_storage = user_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(
        self, request: UpdateNotificationPreferencesRequest,
    ) -> dict[str, Any]:
        logger.info("Update notification preferences: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.profile",
            ),
        )

        user = await self._user_tx_storage.get_by_id(
            UserId(current_user.id_), for_update=True,
        )
        if user is None:
            raise UserNotFoundError

        user.notification_preferences = request.preferences
        user.updated_at = UtcDatetime(self._utc_timer.now.value)
        await self._transaction_manager.commit()

        logger.info("Update notification preferences: done.")
        return user.notification_preferences
