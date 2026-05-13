import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.investor import InvestorQm
from app.core.queries.ports.investor_reader import InvestorReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetInvestorRequest:
    investor_id: UUID


class GetInvestor:
    def __init__(self, investor_reader: InvestorReader) -> None:
        self._investor_reader = investor_reader

    async def execute(self, request: GetInvestorRequest) -> InvestorQm | None:
        logger.info("Get investor: started.")

        result = await self._investor_reader.get_by_id(
            investor_id=request.investor_id,
        )

        logger.info("Get investor: done.")
        return result
