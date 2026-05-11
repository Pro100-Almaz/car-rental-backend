from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.queries.list_fines import ListFines, ListFinesRequest
from app.core.queries.ports.fine_reader import ListFinesQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ListFinesRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_id: UUID
    vehicle_id: UUID | None = None
    client_id: UUID | None = None
    status: str | None = None


def make_list_fines_router() -> APIRouter:
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
    async def list_fines(
        request_schema: Annotated[ListFinesRequestSchema, Depends()],
        interactor: FromDishka[ListFines],
    ) -> ListFinesQm:
        request = ListFinesRequest(
            organization_id=request_schema.organization_id,
            vehicle_id=request_schema.vehicle_id,
            client_id=request_schema.client_id,
            status=request_schema.status,
        )
        return await interactor.execute(request)

    return router
