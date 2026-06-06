from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.client_tx_storage import ClientTxStorage
from app.core.common.entities.client import Client
from app.core.common.entities.types_ import ClientId, UserId
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.client import clients_table


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

    async def get_by_user_id(
        self,
        user_id: UserId,
        *,
        for_update: bool = False,
    ) -> Client | None:
        stmt = select(Client).where(clients_table.c.user_id == user_id)
        if for_update:
            stmt = stmt.with_for_update()
        try:
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise StorageError from e
