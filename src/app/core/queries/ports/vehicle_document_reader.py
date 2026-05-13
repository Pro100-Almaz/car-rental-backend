from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.queries.models.vehicle_document import ListVehicleDocumentsQm


class VehicleDocumentReader(Protocol):
    @abstractmethod
    async def list_documents(
        self,
        *,
        vehicle_id: UUID,
    ) -> ListVehicleDocumentsQm: ...
