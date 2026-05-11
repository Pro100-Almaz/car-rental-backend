from abc import abstractmethod
from typing import Protocol

from app.core.common.entities.branch import Branch
from app.core.common.entities.types_ import BranchId


class BranchTxStorage(Protocol):
    @abstractmethod
    def add(self, branch: Branch) -> None: ...

    @abstractmethod
    async def get_by_id(
        self,
        branch_id: BranchId,
        *,
        for_update: bool = False,
    ) -> Branch | None: ...
