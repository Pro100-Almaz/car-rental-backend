from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.rental_service import RentalServiceQm


class ListRentalServicesQm(TypedDict):
    rental_services: list[RentalServiceQm]
    total: int


class RentalServiceReader(Protocol):
    @abstractmethod
    async def list_rental_services(
        self,
        *,
        rental_id: UUID,
    ) -> ListRentalServicesQm: ...
