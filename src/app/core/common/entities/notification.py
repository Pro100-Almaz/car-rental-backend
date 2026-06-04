from typing import Any

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    NotificationId,
    NotificationType,
    OrganizationId,
    UserId,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class Notification(Entity[NotificationId]):
    def __init__(
        self,
        *,
        id_: NotificationId,
        user_id: UserId,
        organization_id: OrganizationId,
        type_: NotificationType,
        title: str,
        body: str,
        deep_link: str | None,
        metadata: dict[str, Any] | None,
        is_read: bool,
        read_at: UtcDatetime | None,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.user_id = user_id
        self.organization_id = organization_id
        self.type_ = type_
        self.title = title
        self.body = body
        self.deep_link = deep_link
        self.metadata = metadata
        self.is_read = is_read
        self.read_at = read_at
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
