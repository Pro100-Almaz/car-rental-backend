from abc import abstractmethod
from datetime import datetime
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.rental import RentalQm


class ListRentalsQm(TypedDict):
    rentals: list[RentalQm]
    total: int


class SchedulerRentalQm(TypedDict):
    id: UUID
    client_id: UUID
    scheduled_start: datetime
    scheduled_end: datetime


class RentalReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        rental_id: UUID,
    ) -> RentalQm | None: ...

    @abstractmethod
    async def list_rentals(
        self,
        *,
        organization_id: UUID,
        status: str | None = None,
        vehicle_id: UUID | None = None,
        client_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> ListRentalsQm: ...

    @abstractmethod
    async def list_confirmed_starting_between(
        self,
        *,
        organization_id: UUID,
        start_from: datetime,
        start_to: datetime,
    ) -> list[SchedulerRentalQm]: ...

    @abstractmethod
    async def list_active_ending_between(
        self,
        *,
        organization_id: UUID,
        end_from: datetime,
        end_to: datetime,
    ) -> list[SchedulerRentalQm]: ...

    @abstractmethod
    async def list_active_overdue(
        self,
        *,
        organization_id: UUID,
        overdue_before: datetime,
    ) -> list[SchedulerRentalQm]: ...
