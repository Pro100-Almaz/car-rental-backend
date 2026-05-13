import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.vehicle_timeline import VehicleTimelineQm
from app.core.queries.ports.vehicle_timeline_reader import VehicleTimelineReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetVehicleTimelineRequest:
    vehicle_id: UUID


class GetVehicleTimeline:
    def __init__(
        self,
        vehicle_timeline_reader: VehicleTimelineReader,
    ) -> None:
        self._reader = vehicle_timeline_reader

    async def execute(self, request: GetVehicleTimelineRequest) -> VehicleTimelineQm:
        logger.info("Get vehicle timeline: started.")

        result = await self._reader.get_timeline(
            vehicle_id=request.vehicle_id,
        )

        logger.info("Get vehicle timeline: done.")
        return result
