from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.fine import FineQm


class ListFinesQm(TypedDict):
    fines: list[FineQm]
    total: int


class FineReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        fine_id: UUID,
    ) -> FineQm | None: ...

    @abstractmethod
    async def list_fines(
        self,
        *,
        organization_id: UUID,
        vehicle_id: UUID | None = None,
        client_id: UUID | None = None,
        status: str | None = None,
    ) -> ListFinesQm: ...
