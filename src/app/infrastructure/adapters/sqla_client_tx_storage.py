from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.common.entities.client import Client
from app.core.common.entities.types_ import ClientId
from app.infrastructure.exceptions import StorageError


class SqlaClientTxStorage(ClientTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, client: Client) -> None:
        try:
            self._session.add(client)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        client_id: ClientId,
        *,
        for_update: bool = False,
    ) -> Client | None:
        try:
            return await self._session.get(
                Client,
                client_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
