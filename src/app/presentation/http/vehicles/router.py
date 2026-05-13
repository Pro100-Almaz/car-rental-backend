from fastapi import APIRouter

from app.presentation.http.vehicles.bulk_change_status import make_bulk_change_status_router
from app.presentation.http.vehicles.change_vehicle_status import make_change_vehicle_status_router
from app.presentation.http.vehicles.create_vehicle import make_create_vehicle_router
from app.presentation.http.vehicles.get_vehicle import make_get_vehicle_router
from app.presentation.http.vehicles.get_vehicle_financials import make_get_vehicle_financials_router
from app.presentation.http.vehicles.get_vehicle_timeline import make_get_vehicle_timeline_router
from app.presentation.http.vehicles.list_vehicles import make_list_vehicles_router
from app.presentation.http.vehicles.manage_photos import make_manage_photos_router
from app.presentation.http.vehicles.update_vehicle import make_update_vehicle_router


def make_vehicles_router() -> APIRouter:
    router = APIRouter(
        prefix="/vehicles",
        tags=["Vehicles"],
    )
    router.include_router(make_bulk_change_status_router())
    router.include_router(make_create_vehicle_router())
    router.include_router(make_list_vehicles_router())
    router.include_router(make_get_vehicle_router())
    router.include_router(make_update_vehicle_router())
    router.include_router(make_change_vehicle_status_router())
    router.include_router(make_get_vehicle_financials_router())
    router.include_router(make_get_vehicle_timeline_router())
    router.include_router(make_manage_photos_router())
    return router
