from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.common.entities.vehicle_category import VehicleCategoryEntity


class VehicleCategoryTxStorage(Protocol):
    @abstractmethod
    def add(self, category: VehicleCategoryEntity) -> None: ...

    @abstractmethod
    async def get_by_id(self, category_id: UUID) -> VehicleCategoryEntity | None: ...
