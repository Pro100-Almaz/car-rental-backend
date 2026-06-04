import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.queries.ports.rental_reader import ListRentalsQm, RentalReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListRentalsRequest:
    organization_id: UUID
    status: str | None = None
    vehicle_id: UUID | None = None
    client_id: UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class ListRentals:
    def __init__(
        self,
        rental_reader: RentalReader,
    ) -> None:
        self._rental_reader = rental_reader

    async def execute(self, request: ListRentalsRequest) -> ListRentalsQm:
        logger.info("List rentals: started.")

        result = await self._rental_reader.list_rentals(
            organization_id=request.organization_id,
            status=request.status,
            vehicle_id=request.vehicle_id,
            client_id=request.client_id,
            date_from=request.date_from,
            date_to=request.date_to,
        )

        logger.info("List rentals: done.")
        return result
