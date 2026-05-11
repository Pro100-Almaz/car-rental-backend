from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.queries.list_branches import ListBranches, ListBranchesRequest
from app.core.queries.ports.branch_reader import ListBranchesQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ListBranchesRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_id: UUID


def make_list_branches_router() -> APIRouter:
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
    async def list_branches(
        request_schema: Annotated[ListBranchesRequestSchema, Depends()],
        interactor: FromDishka[ListBranches],
    ) -> ListBranchesQm:
        request = ListBranchesRequest(organization_id=request_schema.organization_id)
        return await interactor.execute(request)

    return router
