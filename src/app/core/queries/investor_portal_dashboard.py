import calendar
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.exceptions import InvestorNotFoundError
from app.core.queries.get_investor_pnl import GetInvestorPnl, GetInvestorPnlRequest
from app.core.queries.models.investor_pnl import InvestorPnlQm
from app.core.queries.ports.investor_reader import InvestorReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class InvestorPortalDashboardRequest:
    date_from: date | None = None
    date_to: date | None = None


class InvestorPortalDashboard:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        investor_reader: InvestorReader,
        get_investor_pnl: GetInvestorPnl,
    ) -> None:
        self._current_user_service = current_user_service
        self._investor_reader = investor_reader
        self._get_investor_pnl = get_investor_pnl

    async def execute(self, request: InvestorPortalDashboardRequest) -> InvestorPnlQm:
        logger.info("Investor portal dashboard: started.")

        current_user = await self._current_user_service.get_current_user()
        investor = await self._investor_reader.get_by_user_id(user_id=current_user.id_)
        if investor is None:
            raise InvestorNotFoundError

        date_from = request.date_from
        date_to = request.date_to
        if date_from is None or date_to is None:
            today = datetime.now(tz=UTC).date()
            date_from = date(today.year, today.month, 1)
            date_to = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

        result = await self._get_investor_pnl.execute(
            GetInvestorPnlRequest(
                investor_id=investor.id,
                date_from=date_from,
                date_to=date_to,
            )
        )

        logger.info("Investor portal dashboard: done.")
        return result
