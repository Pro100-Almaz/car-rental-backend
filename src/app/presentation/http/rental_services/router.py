from fastapi import APIRouter

from app.presentation.http.rental_services.add_rental_service import make_add_rental_service_router
from app.presentation.http.rental_services.list_rental_services import make_list_rental_services_router
from app.presentation.http.rental_services.remove_rental_service import make_remove_rental_service_router


def make_rental_services_router() -> APIRouter:
    router = APIRouter(
        prefix="/rental-services",
        tags=["Rental Services"],
    )
    router.include_router(make_add_rental_service_router())
    router.include_router(make_list_rental_services_router())
    router.include_router(make_remove_rental_service_router())
    return router
