import logging

from app.core.commands.exceptions import InvestorNotFoundError
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.queries.ports.investor_reader import InvestorReader, ListVehicleInvestorsQm

logger = logging.getLogger(__name__)


class InvestorPortalVehicles:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        investor_reader: InvestorReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._investor_reader = investor_reader

    async def execute(self) -> ListVehicleInvestorsQm:
        logger.info("Investor portal vehicles: started.")

        current_user = await self._current_user_service.get_current_user()
        investor = await self._investor_reader.get_by_user_id(user_id=current_user.id_)
        if investor is None:
            raise InvestorNotFoundError

        result = await self._investor_reader.list_vehicle_investors(
            investor_id=investor.id,
        )

        logger.info("Investor portal vehicles: done.")
        return result
