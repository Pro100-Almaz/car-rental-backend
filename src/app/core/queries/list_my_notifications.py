import logging
from dataclasses import dataclass

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.notification_reader import ListNotificationsQm, NotificationReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListMyNotificationsRequest:
    limit: int = 20
    offset: int = 0


class ListMyNotifications:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        notification_reader: NotificationReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._notification_reader = notification_reader

    async def execute(self, request: ListMyNotificationsRequest) -> ListNotificationsQm:
        logger.info("List my notifications: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.notifications",
            ),
        )

        result = await self._notification_reader.list_by_user(
            user_id=current_user.id_,
            limit=request.limit,
            offset=request.offset,
        )

        logger.info("List my notifications: done.")
        return result
