from fastapi import APIRouter

from app.presentation.http.additional_services.create_additional_service import make_create_additional_service_router
from app.presentation.http.additional_services.list_additional_services import make_list_additional_services_router
from app.presentation.http.additional_services.update_additional_service import make_update_additional_service_router


def make_additional_services_router() -> APIRouter:
    router = APIRouter(
        prefix="/additional-services",
        tags=["Additional Services"],
    )
    router.include_router(make_create_additional_service_router())
    router.include_router(make_list_additional_services_router())
    router.include_router(make_update_additional_service_router())
    return router
