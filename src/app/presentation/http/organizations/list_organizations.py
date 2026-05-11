from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict, Field

from app.core.queries.list_organizations import (
    ListOrganizations,
    ListOrganizationsRequest,
    OrganizationSortingField,
)
from app.core.queries.ports.organization_reader import ListOrganizationsQm
from app.core.queries.query_support.offset_pagination import OffsetPaginationParams
from app.core.queries.query_support.sorting import SortingOrder
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ListOrganizationsRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    limit: Annotated[int, Field(ge=1, le=OffsetPaginationParams.MAX_INT32)] = 20
    offset: Annotated[int, Field(ge=0, le=OffsetPaginationParams.MAX_INT32)] = 0
    sorting_field: Annotated[OrganizationSortingField, Field()] = OrganizationSortingField.CREATED_AT
    sorting_order: Annotated[SortingOrder, Field()] = SortingOrder.DESC


def make_list_organizations_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_organizations(
        request_schema: Annotated[ListOrganizationsRequestSchema, Depends()],
        interactor: FromDishka[ListOrganizations],
    ) -> ListOrganizationsQm:
        request = ListOrganizationsRequest(
            limit=request_schema.limit,
            offset=request_schema.offset,
            sorting_field=request_schema.sorting_field,
            sorting_order=request_schema.sorting_order,
        )
        return await interactor.execute(request)

    return router
