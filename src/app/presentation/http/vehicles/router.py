from fastapi import APIRouter

from app.presentation.http.vehicles.change_vehicle_status import make_change_vehicle_status_router
from app.presentation.http.vehicles.create_vehicle import make_create_vehicle_router
from app.presentation.http.vehicles.get_vehicle import make_get_vehicle_router
from app.presentation.http.vehicles.list_vehicles import make_list_vehicles_router
from app.presentation.http.vehicles.update_vehicle import make_update_vehicle_router


def make_vehicles_router() -> APIRouter:
    router = APIRouter(
        prefix="/vehicles",
        tags=["Vehicles"],
    )
    router.include_router(make_create_vehicle_router())
    router.include_router(make_list_vehicles_router())
    router.include_router(make_get_vehicle_router())
    router.include_router(make_update_vehicle_router())
    router.include_router(make_change_vehicle_status_router())
    return router
