from fastapi import APIRouter

from app.presentation.http.vehicle_pricing.create_vehicle_pricing import make_create_vehicle_pricing_router
from app.presentation.http.vehicle_pricing.list_vehicle_pricing import make_list_vehicle_pricing_router
from app.presentation.http.vehicle_pricing.update_vehicle_pricing import make_update_vehicle_pricing_router


def make_vehicle_pricing_router() -> APIRouter:
    router = APIRouter(prefix="/vehicle-pricing", tags=["Vehicle Pricing"])
    router.include_router(make_create_vehicle_pricing_router())
    router.include_router(make_list_vehicle_pricing_router())
    router.include_router(make_update_vehicle_pricing_router())
    return router
