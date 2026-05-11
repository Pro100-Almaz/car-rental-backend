import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.rental import RentalQm
from app.core.queries.ports.rental_reader import RentalReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetRentalRequest:
    rental_id: UUID


class GetRental:
    def __init__(
        self,
        rental_reader: RentalReader,
    ) -> None:
        self._rental_reader = rental_reader

    async def execute(self, request: GetRentalRequest) -> RentalQm | None:
        logger.info("Get rental: started.")

        result = await self._rental_reader.get_by_id(
            rental_id=request.rental_id,
        )

        logger.info("Get rental: done.")
        return result
