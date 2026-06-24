from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commands.ports.client_document_tx_storage import ClientDocumentTxStorage
from app.core.common.entities.client_documents import ClientDocument
from app.infrastructure.exceptions import StorageError


class SqlaClientDocumentTxStorage(ClientDocumentTxStorage):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, client_document: ClientDocument) -> None:
        self._session.add(client_document)

    def batch_add(self, client_documents: list[ClientDocument]) -> None:
        self._session.add_all(client_documents)

    async def get_by_id(self, document_id: UUID) -> ClientDocument | None:
        try:
            return await self._session.get(ClientDocument, document_id)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def delete(self, client_document: ClientDocument) -> None:
        try:
            await self._session.delete(client_document)
        except SQLAlchemyError as e:
            raise StorageError from e

    async def flush(self) -> None:
        try:
            await self._session.flush()
        except SQLAlchemyError as e:
            raise StorageError from e
