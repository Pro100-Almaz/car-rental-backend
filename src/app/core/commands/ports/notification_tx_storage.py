from typing import Protocol

from app.core.common.entities.notification import Notification
from app.core.common.entities.types_ import NotificationId


class NotificationTxStorage(Protocol):
    def add(self, notification: Notification) -> None: ...

    async def get_by_id(
        self,
        notification_id: NotificationId,
        *,
        for_update: bool = False,
    ) -> Notification | None: ...
