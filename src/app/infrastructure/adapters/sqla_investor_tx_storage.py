from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.investor_tx_storage import InvestorTxStorage
from app.core.common.entities.investor import Investor
from app.core.common.entities.types_ import InvestorId
from app.infrastructure.exceptions import StorageError


class SqlaInvestorTxStorage(InvestorTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, investor: Investor) -> None:
        try:
            self._session.add(investor)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        investor_id: InvestorId,
        *,
        for_update: bool = False,
    ) -> Investor | None:
        try:
            return await self._session.get(
                Investor,
                investor_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
