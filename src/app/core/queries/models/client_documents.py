from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ClientDocumentQm:
    id: UUID
    client_id: UUID
    status: str
    name: str
    description: str | None
    url: str | None
    document_type: str
    _created_at: datetime
    _updated_at: datetime


@dataclass(frozen=True, slots=True)
class ClientDocumentListItemQm:
    id: UUID | None
    name: str
    status: str
    description: str | None
    document_type: str
    url: str | None


@dataclass(frozen=True, slots=True)
class GetClientDocumentsQm:
    national_id: ClientDocumentListItemQm
    license_front: ClientDocumentListItemQm
    license_back: ClientDocumentListItemQm
