from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.organization import OrganizationQm


class ListClientOrganizationsQm(TypedDict):
    organizations: list[OrganizationQm]
    total: int


class ClientOrganizationReader(Protocol):
    @abstractmethod
    async def list_by_client_id(
        self,
        *,
        client_id: UUID,
    ) -> ListClientOrganizationsQm: ...

    @abstractmethod
    async def list_organization_ids_for_client(
        self,
        *,
        client_id: UUID,
    ) -> list[UUID]: ...
