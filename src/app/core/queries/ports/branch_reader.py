from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.branch import BranchQm


class ListBranchesQm(TypedDict):
    branches: list[BranchQm]
    total: int


class BranchReader(Protocol):
    @abstractmethod
    async def list_branches(
        self,
        *,
        organization_id: UUID,
    ) -> ListBranchesQm: ...
