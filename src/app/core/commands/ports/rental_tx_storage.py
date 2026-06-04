from datetime import datetime
from typing import Protocol

from app.core.common.entities.rental import Rental
from app.core.common.entities.types_ import RentalId, VehicleId


class RentalTxStorage(Protocol):
    def add(self, rental: Rental) -> None: ...

    async def get_by_id(
        self,
        rental_id: RentalId,
        *,
        for_update: bool = False,
    ) -> Rental | None: ...

    async def has_overlap(
        self,
        vehicle_id: VehicleId,
        scheduled_start: datetime,
        scheduled_end: datetime,
    ) -> bool: ...
