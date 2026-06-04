from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.extension_request_tx_storage import ExtensionRequestTxStorage
from app.core.common.entities.extension_request import ExtensionRequest
from app.core.common.entities.types_ import ExtensionRequestId, ExtensionRequestStatus, RentalId
from app.infrastructure.exceptions import StorageError
from app.infrastructure.persistence_sqla.mappings.extension_request import extension_requests_table


class SqlaExtensionRequestTxStorage(ExtensionRequestTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, extension_request: ExtensionRequest) -> None:
        try:
            self._session.add(extension_request)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_by_id(
        self,
        extension_request_id: ExtensionRequestId,
        *,
        for_update: bool = False,
    ) -> ExtensionRequest | None:
        try:
            return await self._session.get(
                ExtensionRequest,
                extension_request_id,
                with_for_update=for_update,
            )
        except SQLAlchemyError as e:
            raise StorageError from e

    async def get_pending_for_rental(
        self,
        rental_id: RentalId,
    ) -> ExtensionRequest | None:
        try:
            stmt = (
                select(ExtensionRequest)
                .where(extension_requests_table.c.rental_id == rental_id)
                .where(extension_requests_table.c.status == ExtensionRequestStatus.PENDING)
                .limit(1)
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise StorageError from e
