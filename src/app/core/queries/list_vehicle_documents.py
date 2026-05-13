import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.vehicle_document import ListVehicleDocumentsQm
from app.core.queries.ports.vehicle_document_reader import VehicleDocumentReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListVehicleDocumentsRequest:
    vehicle_id: UUID


class ListVehicleDocuments:
    def __init__(
        self,
        vehicle_document_reader: VehicleDocumentReader,
    ) -> None:
        self._reader = vehicle_document_reader

    async def execute(self, request: ListVehicleDocumentsRequest) -> ListVehicleDocumentsQm:
        logger.info("List vehicle documents: started.")

        result = await self._reader.list_documents(
            vehicle_id=request.vehicle_id,
        )

        logger.info("List vehicle documents: done.")
        return result
