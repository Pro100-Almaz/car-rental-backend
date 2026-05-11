from abc import abstractmethod
from typing import Protocol, TypedDict

from app.core.queries.models.organization import OrganizationQm
from app.core.queries.query_support.offset_pagination import OffsetPaginationParams
from app.core.queries.query_support.sorting import SortingParams


class ListOrganizationsQm(TypedDict):
    organizations: list[OrganizationQm]
    total: int
    limit: int
    offset: int


class OrganizationReader(Protocol):
    @abstractmethod
    async def list_organizations(
        self,
        *,
        pagination: OffsetPaginationParams,
        sorting: SortingParams,
    ) -> ListOrganizationsQm: ...
