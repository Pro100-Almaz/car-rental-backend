from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import ClientDocumentId, ClientDocumentStatus, ClientDocumentType, ClientId
from app.core.common.value_objects.utc_datetime import UtcDatetime


class ClientDocument(Entity[ClientDocumentId]):
    def __init__(
        self,
        *,
        id_: ClientDocumentId,
        client_id: ClientId,
        status: ClientDocumentStatus,
        document_type: ClientDocumentType,
        name: str,
        description: str | None,
        url: str,
        created_at: UtcDatetime,
        updated_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.client_id = client_id
        self.status = status
        self.url = url
        self.name = name
        self.description = description
        self.document_type = document_type
        self._created_at = created_at
        self._updated_at = updated_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at

    @property
    def updated_at(self) -> UtcDatetime:
        return self._updated_at

    def update_name(self, name: str) -> None:
        self.name = name

    def update_file_url(self, url: str, updated_at: UtcDatetime) -> None:
        self.url = url
        self._updated_at = updated_at

    def update_metadata(
        self,
        *,
        name: str,
        status: ClientDocumentStatus,
        updated_at: UtcDatetime,
        description: str | None,
    ) -> None:
        self.name = name
        self.status = status
        self._updated_at = updated_at
        self.description = description
