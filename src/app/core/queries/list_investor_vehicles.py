import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.investor_reader import InvestorReader, ListVehicleInvestorsQm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListInvestorVehiclesRequest:
    investor_id: UUID


class ListInvestorVehicles:
    def __init__(self, investor_reader: InvestorReader) -> None:
        self._investor_reader = investor_reader

    async def execute(self, request: ListInvestorVehiclesRequest) -> ListVehicleInvestorsQm:
        logger.info("List investor vehicles: started.")

        result = await self._investor_reader.list_vehicle_investors(
            investor_id=request.investor_id,
        )

        logger.info("List investor vehicles: done.")
        return result
