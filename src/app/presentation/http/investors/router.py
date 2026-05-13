from fastapi import APIRouter

from app.presentation.http.investors.bind_vehicle import make_bind_vehicle_router
from app.presentation.http.investors.create_investor import make_create_investor_router
from app.presentation.http.investors.create_payout import make_create_payout_router
from app.presentation.http.investors.get_investor import make_get_investor_router
from app.presentation.http.investors.list_investor_vehicles import make_list_investor_vehicles_router
from app.presentation.http.investors.list_investors import make_list_investors_router
from app.presentation.http.investors.list_payouts import make_list_payouts_router
from app.presentation.http.investors.unbind_vehicle import make_unbind_vehicle_router
from app.presentation.http.investors.update_investor import make_update_investor_router
from app.presentation.http.investors.update_payout_status import make_update_payout_status_router


def make_investors_router() -> APIRouter:
    router = APIRouter(
        prefix="/investors",
        tags=["Investors"],
    )
    router.include_router(make_create_investor_router())
    router.include_router(make_list_investors_router())
    router.include_router(make_get_investor_router())
    router.include_router(make_update_investor_router())
    router.include_router(make_bind_vehicle_router())
    router.include_router(make_unbind_vehicle_router())
    router.include_router(make_list_investor_vehicles_router())
    router.include_router(make_create_payout_router())
    router.include_router(make_list_payouts_router())
    router.include_router(make_update_payout_status_router())
    return router
