import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.vehicle_reader import ListVehiclesQm, VehicleReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListVehiclesRequest:
    organization_id: UUID
    status: str | None = None
    branch_id: UUID | None = None


class ListVehicles:
    def __init__(
        self,
        vehicle_reader: VehicleReader,
    ) -> None:
        self._vehicle_reader = vehicle_reader

    async def execute(self, request: ListVehiclesRequest) -> ListVehiclesQm:
        logger.info("List vehicles: started.")

        result = await self._vehicle_reader.list_vehicles(
            organization_id=request.organization_id,
            status=request.status,
            branch_id=request.branch_id,
        )

        logger.info("List vehicles: done.")
        return result
