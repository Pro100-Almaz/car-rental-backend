import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.core.queries.models.report_pnl import CompanyPnlQm
from app.core.queries.ports.report_reader import ReportReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetCompanyPnlRequest:
    organization_id: UUID
    date_from: date
    date_to: date


class GetCompanyPnl:
    def __init__(
        self,
        report_reader: ReportReader,
    ) -> None:
        self._report_reader = report_reader

    async def execute(self, request: GetCompanyPnlRequest) -> CompanyPnlQm:
        logger.info("Get company PnL: started.")

        result = await self._report_reader.get_company_pnl(
            organization_id=request.organization_id,
            date_from=request.date_from,
            date_to=request.date_to,
        )

        logger.info("Get company PnL: done.")
        return result
