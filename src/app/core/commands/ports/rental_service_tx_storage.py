from typing import Protocol

from app.core.common.entities.rental_service import RentalService
from app.core.common.entities.types_ import RentalServiceId


class RentalServiceTxStorage(Protocol):
    def add(self, rental_service: RentalService) -> None: ...

    async def get_by_id(
        self,
        rental_service_id: RentalServiceId,
        *,
        for_update: bool = False,
    ) -> RentalService | None: ...

    async def delete(self, rental_service: RentalService) -> None: ...
