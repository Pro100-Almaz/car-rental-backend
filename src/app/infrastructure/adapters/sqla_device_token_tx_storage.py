from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.device_token_tx_storage import DeviceTokenTxStorage
from app.core.common.entities.device_token import DeviceToken
from app.core.common.entities.types_ import DeviceTokenId, UserId
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.device_token import device_tokens_table


class SqlaDeviceTokenTxStorage(DeviceTokenTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, device_token: DeviceToken) -> None:
        try:
            self._session.add(device_token)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        device_token_id: DeviceTokenId,
        *,
        for_update: bool = False,
    ) -> DeviceToken | None:
        try:
            return await self._session.get(
                DeviceToken,
                device_token_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_token(self, token: str) -> DeviceToken | None:
        try:
            stmt = select(DeviceToken).where(device_tokens_table.c.token == token)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise StorageError from e

    async def delete_by_token(self, token: str, user_id: UserId) -> bool:
        try:
            stmt = (
                delete(device_tokens_table)
                .where(device_tokens_table.c.token == token)
                .where(device_tokens_table.c.user_id == user_id)
            )
            result = await self._session.execute(stmt)
            return result.rowcount > 0
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_all_for_user(self, user_id: UserId) -> list[DeviceToken]:
        try:
            stmt = select(DeviceToken).where(device_tokens_table.c.user_id == user_id)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise StorageError from e
