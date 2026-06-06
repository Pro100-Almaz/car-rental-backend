from typing import Protocol

from app.core.common.entities.client import Client
from app.core.common.entities.types_ import ClientId, UserId


class ClientTxStorage(Protocol):
    def add(self, client: Client) -> None: ...

    async def get_by_id(
        self,
        client_id: ClientId,
        *,
        for_update: bool = False,
    ) -> Client | None: ...

    async def get_by_user_id(
        self,
        user_id: UserId,
        *,
        for_update: bool = False,
    ) -> Client | None: ...
