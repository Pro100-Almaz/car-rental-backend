from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.mobile_rental import MobileRentalQm


class ListMobileRentalsQm(TypedDict):
    rentals: list[MobileRentalQm]
    total: int


class MobileRentalReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        rental_id: UUID,
        client_id: UUID,
    ) -> MobileRentalQm | None: ...

    @abstractmethod
    async def list_by_client(
        self,
        *,
        client_id: UUID,
        status: str | None = None,
    ) -> ListMobileRentalsQm: ...

    @abstractmethod
    async def get_active_by_client(
        self,
        *,
        client_id: UUID,
    ) -> MobileRentalQm | None: ...
