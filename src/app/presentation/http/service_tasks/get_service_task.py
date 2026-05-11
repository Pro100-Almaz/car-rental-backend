from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_service_task import GetServiceTask, GetServiceTaskRequest
from app.core.queries.models.service_task import ServiceTaskQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_service_task_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{service_task_id}",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "Service task not found"}},
    )
    @inject
    async def get_service_task(
        service_task_id: UUID,
        interactor: FromDishka[GetServiceTask],
    ) -> ServiceTaskQm:
        result = await interactor.execute(GetServiceTaskRequest(service_task_id=service_task_id))
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service task not found.")
        return result

    return router
