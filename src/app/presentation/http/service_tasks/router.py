from fastapi import APIRouter

from app.presentation.http.service_tasks.complete_service_task import make_complete_service_task_router
from app.presentation.http.service_tasks.create_service_task import make_create_service_task_router
from app.presentation.http.service_tasks.get_service_task import make_get_service_task_router
from app.presentation.http.service_tasks.list_service_tasks import make_list_service_tasks_router
from app.presentation.http.service_tasks.update_service_task import make_update_service_task_router


def make_service_tasks_router() -> APIRouter:
    router = APIRouter(
        prefix="/tasks",
        tags=["Service Tasks"],
    )
    router.include_router(make_create_service_task_router())
    router.include_router(make_list_service_tasks_router())
    router.include_router(make_get_service_task_router())
    router.include_router(make_update_service_task_router())
    router.include_router(make_complete_service_task_router())
    return router
