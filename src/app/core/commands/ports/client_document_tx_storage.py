from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.common.entities.client_documents import ClientDocument


class ClientDocumentTxStorage(Protocol):
    @abstractmethod
    def add(self, client_document: ClientDocument) -> None: ...

    @abstractmethod
    def batch_add(self, client_documents: list[ClientDocument]) -> None: ...

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> ClientDocument | None: ...

    @abstractmethod
    async def delete(self, client_document: ClientDocument) -> None: ...

    @abstractmethod
    async def flush(self) -> None: ...
