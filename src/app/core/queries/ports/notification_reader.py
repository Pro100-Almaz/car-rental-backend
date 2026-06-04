from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.notification import NotificationQm


class ListNotificationsQm(TypedDict):
    notifications: list[NotificationQm]
    total: int
    unread_count: int


class NotificationReader(Protocol):
    @abstractmethod
    async def list_by_user(
        self,
        *,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> ListNotificationsQm: ...
