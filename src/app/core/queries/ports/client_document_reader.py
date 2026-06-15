from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.queries.models.client_documents import GetClientDocumentsQm


class ClientDocumentReader(Protocol):
    @abstractmethod
    async def list_client_documents(self, *, client_id: UUID) -> GetClientDocumentsQm: ...
