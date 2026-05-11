from datetime import datetime
from decimal import Decimal
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import InvalidTaskStatusTransitionError, ServiceTaskNotFoundError
from app.core.commands.update_service_task import UpdateServiceTask, UpdateServiceTaskRequest
from app.core.common.entities.types_ import TaskPriority, TaskStatus
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class UpdateServiceTaskBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    assigned_to: UUID | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    description: str | None = None
    estimated_cost: Decimal | None = None
    actual_cost: Decimal | None = None
    notes: str | None = None
    due_at: datetime | None = None


def make_update_service_task_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{service_task_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            ServiceTaskNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidTaskStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def update_service_task(
        service_task_id: UUID,
        body: UpdateServiceTaskBody,
        interactor: FromDishka[UpdateServiceTask],
    ) -> None:
        kwargs: dict[str, object] = {"service_task_id": service_task_id}
        for field_name in body.model_fields_set:
            kwargs[field_name] = getattr(body, field_name)
        request = UpdateServiceTaskRequest(**kwargs)  # type: ignore[arg-type]
        await interactor.execute(request)

    return router
