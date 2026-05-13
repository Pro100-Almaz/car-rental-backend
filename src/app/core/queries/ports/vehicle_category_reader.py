from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.queries.models.vehicle_category import ListVehicleCategoriesQm


class VehicleCategoryReader(Protocol):
    @abstractmethod
    async def list_categories(
        self,
        *,
        organization_id: UUID,
    ) -> ListVehicleCategoriesQm: ...
