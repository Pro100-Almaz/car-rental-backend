from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.client import ClientQm


class ListClientsQm(TypedDict):
    clients: list[ClientQm]
    total: int


class ClientReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        client_id: UUID,
    ) -> ClientQm | None: ...

    @abstractmethod
    async def list_clients(
        self,
        *,
        organization_id: UUID,
        verification_status: str | None = None,
        is_blacklisted: bool | None = None,
    ) -> ListClientsQm: ...
