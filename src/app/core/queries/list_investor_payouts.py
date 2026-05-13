import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.investor_reader import InvestorReader, ListInvestorPayoutsQm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListInvestorPayoutsRequest:
    investor_id: UUID
    status: str | None = None


class ListInvestorPayouts:
    def __init__(self, investor_reader: InvestorReader) -> None:
        self._investor_reader = investor_reader

    async def execute(self, request: ListInvestorPayoutsRequest) -> ListInvestorPayoutsQm:
        logger.info("List investor payouts: started.")

        result = await self._investor_reader.list_investor_payouts(
            investor_id=request.investor_id,
            status=request.status,
        )

        logger.info("List investor payouts: done.")
        return result
