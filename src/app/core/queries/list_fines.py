import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.fine_reader import FineReader, ListFinesQm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListFinesRequest:
    organization_id: UUID
    vehicle_id: UUID | None = None
    client_id: UUID | None = None
    status: str | None = None


class ListFines:
    def __init__(
        self,
        fine_reader: FineReader,
    ) -> None:
        self._fine_reader = fine_reader

    async def execute(self, request: ListFinesRequest) -> ListFinesQm:
        logger.info("List fines: started.")

        result = await self._fine_reader.list_fines(
            organization_id=request.organization_id,
            vehicle_id=request.vehicle_id,
            client_id=request.client_id,
            status=request.status,
        )

        logger.info("List fines: done.")
        return result
