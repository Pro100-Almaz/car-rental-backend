from typing import Protocol

from app.core.common.entities.rental import Rental
from app.core.common.entities.types_ import RentalId


class RentalTxStorage(Protocol):
    def add(self, rental: Rental) -> None: ...

    async def get_by_id(
        self,
        rental_id: RentalId,
        *,
        for_update: bool = False,
    ) -> Rental | None: ...
