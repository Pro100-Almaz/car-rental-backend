from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.fine_tx_storage import FineTxStorage
from app.core.common.entities.fine import Fine
from app.core.common.entities.types_ import FineId
from app.infrastructure.exceptions import StorageError


class SqlaFineTxStorage(FineTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, fine: Fine) -> None:
        try:
            self._session.add(fine)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        fine_id: FineId,
        *,
        for_update: bool = False,
    ) -> Fine | None:
        try:
            return await self._session.get(
                Fine,
                fine_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
