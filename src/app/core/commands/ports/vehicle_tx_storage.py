from abc import abstractmethod
from typing import Protocol

from app.core.common.entities.types_ import VehicleId
from app.core.common.entities.vehicle import Vehicle


class VehicleTxStorage(Protocol):
    @abstractmethod
    def add(self, vehicle: Vehicle) -> None: ...

    @abstractmethod
    async def get_by_id(
        self,
        vehicle_id: VehicleId,
        *,
        for_update: bool = False,
    ) -> Vehicle | None: ...
