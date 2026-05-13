import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.vehicle_category import ListVehicleCategoriesQm
from app.core.queries.ports.vehicle_category_reader import VehicleCategoryReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListVehicleCategoriesRequest:
    organization_id: UUID


class ListVehicleCategories:
    def __init__(
        self,
        vehicle_category_reader: VehicleCategoryReader,
    ) -> None:
        self._reader = vehicle_category_reader

    async def execute(self, request: ListVehicleCategoriesRequest) -> ListVehicleCategoriesQm:
        logger.info("List vehicle categories: started.")
        result = await self._reader.list_categories(
            organization_id=request.organization_id,
        )
        logger.info("List vehicle categories: done.")
        return result
