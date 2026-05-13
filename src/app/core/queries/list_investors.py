import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.investor_reader import InvestorReader, ListInvestorsQm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListInvestorsRequest:
    organization_id: UUID
    type_: str | None = None


class ListInvestors:
    def __init__(self, investor_reader: InvestorReader) -> None:
        self._investor_reader = investor_reader

    async def execute(self, request: ListInvestorsRequest) -> ListInvestorsQm:
        logger.info("List investors: started.")

        result = await self._investor_reader.list_investors(
            organization_id=request.organization_id,
            type_=request.type_,
        )

        logger.info("List investors: done.")
        return result
