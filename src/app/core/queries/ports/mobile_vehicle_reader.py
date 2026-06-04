from abc import abstractmethod
from datetime import datetime
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.mobile_vehicle import MobileVehicleQm


class ListMobileVehiclesQm(TypedDict):
    vehicles: list[MobileVehicleQm]
    total: int


class VehicleAvailabilityQm(TypedDict):
    vehicle_id: UUID
    is_available: bool
    conflicting_periods: list[dict[str, datetime]]


class MobileVehicleReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        vehicle_id: UUID,
        organization_id: UUID,
    ) -> MobileVehicleQm | None: ...

    @abstractmethod
    async def list_available(
        self,
        *,
        organization_id: UUID,
        category: str | None = None,
        fuel_type: str | None = None,
        transmission: str | None = None,
        branch_id: UUID | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> ListMobileVehiclesQm: ...

    @abstractmethod
    async def check_availability(
        self,
        *,
        vehicle_id: UUID,
        scheduled_start: datetime,
        scheduled_end: datetime,
    ) -> VehicleAvailabilityQm: ...
