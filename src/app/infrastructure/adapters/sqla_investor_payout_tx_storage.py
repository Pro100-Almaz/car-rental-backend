from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.investor_payout_tx_storage import InvestorPayoutTxStorage
from app.core.common.entities.investor_payout import InvestorPayout
from app.core.common.entities.types_ import InvestorPayoutId
from app.infrastructure.exceptions import StorageError


class SqlaInvestorPayoutTxStorage(InvestorPayoutTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, payout: InvestorPayout) -> None:
        try:
            self._session.add(payout)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        payout_id: InvestorPayoutId,
        *,
        for_update: bool = False,
    ) -> InvestorPayout | None:
        try:
            return await self._session.get(
                InvestorPayout,
                payout_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
