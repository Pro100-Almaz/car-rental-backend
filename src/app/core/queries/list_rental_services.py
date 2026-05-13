import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.rental_service_reader import ListRentalServicesQm, RentalServiceReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListRentalServicesRequest:
    rental_id: UUID


class ListRentalServices:
    def __init__(
        self,
        rental_service_reader: RentalServiceReader,
    ) -> None:
        self._rental_service_reader = rental_service_reader

    async def execute(self, request: ListRentalServicesRequest) -> ListRentalServicesQm:
        logger.info("List rental services: started.")

        result = await self._rental_service_reader.list_rental_services(
            rental_id=request.rental_id,
        )

        logger.info("List rental services: done.")
        return result
