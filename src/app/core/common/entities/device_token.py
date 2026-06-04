from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    DevicePlatform,
    DeviceTokenId,
    UserId,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class DeviceToken(Entity[DeviceTokenId]):
    def __init__(
        self,
        *,
        id_: DeviceTokenId,
        user_id: UserId,
        token: str,
        platform: DevicePlatform,
        device_name: str | None,
        last_active_at: UtcDatetime,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.user_id = user_id
        self.token = token
        self.platform = platform
        self.device_name = device_name
        self.last_active_at = last_active_at
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
