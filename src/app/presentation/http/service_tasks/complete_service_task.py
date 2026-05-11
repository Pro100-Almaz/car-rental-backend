from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.complete_service_task import CompleteServiceTask, CompleteServiceTaskRequest
from app.core.commands.exceptions import InvalidTaskStatusTransitionError, ServiceTaskNotFoundError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_complete_service_task_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{service_task_id}/complete",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            ServiceTaskNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidTaskStatusTransitionError: status.HTTP_409_CONFLICT,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def complete_service_task(
        service_task_id: UUID,
        request: CompleteServiceTaskRequest,
        interactor: FromDishka[CompleteServiceTask],
    ) -> None:
        await interactor.execute(request)

    return router
