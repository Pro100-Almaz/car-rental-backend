import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.branch_reader import BranchReader, ListBranchesQm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListBranchesRequest:
    organization_id: UUID


class ListBranches:
    def __init__(
        self,
        branch_reader: BranchReader,
    ) -> None:
        self._branch_reader = branch_reader

    async def execute(self, request: ListBranchesRequest) -> ListBranchesQm:
        logger.info("List branches: started.")

        result = await self._branch_reader.list_branches(
            organization_id=request.organization_id,
        )

        logger.info("List branches: done.")
        return result
