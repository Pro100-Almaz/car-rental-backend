from abc import abstractmethod
from datetime import date
from typing import Protocol
from uuid import UUID

from app.core.queries.models.vehicle_financials import VehicleFinancialsQm


class VehicleFinancialsReader(Protocol):
    @abstractmethod
    async def get_financials(
        self,
        *,
        vehicle_id: UUID,
        date_from: date,
        date_to: date,
    ) -> VehicleFinancialsQm: ...
