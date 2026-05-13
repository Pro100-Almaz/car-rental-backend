from typing import Protocol

from app.core.common.entities.types_ import VehicleInvestorId
from app.core.common.entities.vehicle_investor import VehicleInvestor


class VehicleInvestorTxStorage(Protocol):
    def add(self, vehicle_investor: VehicleInvestor) -> None: ...

    async def get_by_id(
        self,
        vehicle_investor_id: VehicleInvestorId,
        *,
        for_update: bool = False,
    ) -> VehicleInvestor | None: ...

    async def delete(self, vehicle_investor: VehicleInvestor) -> None: ...
