from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.notification_tx_storage import NotificationTxStorage
from app.core.common.entities.notification import Notification
from app.core.common.entities.types_ import NotificationId
from app.infrastructure.exceptions import StorageError


class SqlaNotificationTxStorage(NotificationTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, notification: Notification) -> None:
        try:
            self._session.add(notification)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        notification_id: NotificationId,
        *,
        for_update: bool = False,
    ) -> Notification | None:
        try:
            return await self._session.get(
                Notification,
                notification_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
