from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.queries.models.vehicle_timeline import VehicleTimelineQm


class VehicleTimelineReader(Protocol):
    @abstractmethod
    async def get_timeline(
        self,
        *,
        vehicle_id: UUID,
    ) -> VehicleTimelineQm: ...
