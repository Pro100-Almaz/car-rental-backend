from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.branch_tx_storage import BranchTxStorage
from app.core.common.entities.branch import Branch
from app.core.common.entities.types_ import BranchId
from app.infrastructure.exceptions import StorageError


class SqlaBranchTxStorage(BranchTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, branch: Branch) -> None:
        try:
            self._session.add(branch)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        branch_id: BranchId,
        *,
        for_update: bool = False,
    ) -> Branch | None:
        try:
            return await self._session.get(
                Branch,
                branch_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
