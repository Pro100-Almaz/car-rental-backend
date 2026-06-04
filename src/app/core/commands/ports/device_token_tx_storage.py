from typing import Protocol

from app.core.common.entities.device_token import DeviceToken
from app.core.common.entities.types_ import DeviceTokenId, UserId


class DeviceTokenTxStorage(Protocol):
    def add(self, device_token: DeviceToken) -> None: ...

    async def get_by_id(
        self,
        device_token_id: DeviceTokenId,
        *,
        for_update: bool = False,
    ) -> DeviceToken | None: ...

    async def get_by_token(self, token: str) -> DeviceToken | None: ...

    async def delete_by_token(self, token: str, user_id: UserId) -> bool: ...

    async def get_all_for_user(self, user_id: UserId) -> list[DeviceToken]: ...
