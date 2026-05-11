from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.queries.list_service_tasks import ListServiceTasks, ListServiceTasksRequest
from app.core.queries.ports.service_task_reader import ListServiceTasksQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ListServiceTasksRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_id: UUID
    vehicle_id: UUID | None = None
    assigned_to: UUID | None = None
    status: str | None = None
    priority: str | None = None


def make_list_service_tasks_router() -> APIRouter:
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
    async def list_service_tasks(
        request_schema: Annotated[ListServiceTasksRequestSchema, Depends()],
        interactor: FromDishka[ListServiceTasks],
    ) -> ListServiceTasksQm:
        request = ListServiceTasksRequest(
            organization_id=request_schema.organization_id,
            vehicle_id=request_schema.vehicle_id,
            assigned_to=request_schema.assigned_to,
            status=request_schema.status,
            priority=request_schema.priority,
        )
        return await interactor.execute(request)

    return router
