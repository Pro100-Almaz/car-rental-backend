from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.additional_service import AdditionalServiceQm


class ListAdditionalServicesQm(TypedDict):
    additional_services: list[AdditionalServiceQm]
    total: int


class AdditionalServiceReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        additional_service_id: UUID,
    ) -> AdditionalServiceQm | None: ...

    @abstractmethod
    async def list_additional_services(
        self,
        *,
        organization_id: UUID,
        is_active: bool | None = None,
    ) -> ListAdditionalServicesQm: ...
