from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.common.entities.vehicle_document import VehicleDocument


class VehicleDocumentTxStorage(Protocol):
    @abstractmethod
    def add(self, vehicle_document: VehicleDocument) -> None: ...

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> VehicleDocument | None: ...

    @abstractmethod
    async def delete(self, vehicle_document: VehicleDocument) -> None: ...
