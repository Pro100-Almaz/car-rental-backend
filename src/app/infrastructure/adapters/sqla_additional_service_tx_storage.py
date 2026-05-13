from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.additional_service_tx_storage import AdditionalServiceTxStorage
from app.core.common.entities.additional_service import AdditionalService
from app.core.common.entities.types_ import AdditionalServiceId
from app.infrastructure.exceptions import StorageError


class SqlaAdditionalServiceTxStorage(AdditionalServiceTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, additional_service: AdditionalService) -> None:
        try:
            self._session.add(additional_service)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        additional_service_id: AdditionalServiceId,
        *,
        for_update: bool = False,
    ) -> AdditionalService | None:
        try:
            return await self._session.get(
                AdditionalService,
                additional_service_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e
