import logging
from dataclasses import dataclass
from enum import StrEnum

from app.core.queries.ports.organization_reader import ListOrganizationsQm, OrganizationReader
from app.core.queries.query_support.offset_pagination import OffsetPaginationParams
from app.core.queries.query_support.sorting import SortingOrder, SortingParams

logger = logging.getLogger(__name__)


class OrganizationSortingField(StrEnum):
    NAME = "name"
    SLUG = "slug"
    CREATED_AT = "created_at"


@dataclass(frozen=True, slots=True, kw_only=True)
class ListOrganizationsRequest:
    limit: int
    offset: int
    sorting_field: OrganizationSortingField
    sorting_order: SortingOrder


class ListOrganizations:
    def __init__(
        self,
        organization_reader: OrganizationReader,
    ) -> None:
        self._organization_reader = organization_reader

    async def execute(self, request: ListOrganizationsRequest) -> ListOrganizationsQm:
        logger.info("List organizations: started.")

        pagination = OffsetPaginationParams(
            limit=request.limit,
            offset=request.offset,
        )
        sorting = SortingParams(
            field=request.sorting_field,
            order=request.sorting_order,
        )
        result = await self._organization_reader.list_organizations(
            pagination=pagination,
            sorting=sorting,
        )

        logger.info("List organizations: done.")
        return result
