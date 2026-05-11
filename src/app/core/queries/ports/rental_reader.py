from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.rental import RentalQm


class ListRentalsQm(TypedDict):
    rentals: list[RentalQm]
    total: int


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
    ) -> ListRentalsQm: ...
