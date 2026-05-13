from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.vehicle import VehicleQm


class ListVehiclesQm(TypedDict):
    vehicles: list[VehicleQm]
    total: int


class VehicleReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        vehicle_id: UUID,
    ) -> VehicleQm | None: ...

    @abstractmethod
    async def list_vehicles(
        self,
        *,
        organization_id: UUID,
        status: str | None = None,
        branch_id: UUID | None = None,
        category: str | None = None,
        investor_id: UUID | None = None,
        search: str | None = None,
    ) -> ListVehiclesQm: ...
