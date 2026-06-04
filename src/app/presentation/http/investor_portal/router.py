from fastapi import APIRouter

from app.presentation.http.investor_portal.dashboard import make_portal_dashboard_router
from app.presentation.http.investor_portal.payouts import make_portal_payouts_router
from app.presentation.http.investor_portal.vehicles import make_portal_vehicles_router


def make_investor_portal_router() -> APIRouter:
    router = APIRouter(
        prefix="/investor-portal",
        tags=["Investor Portal"],
    )
    router.include_router(make_portal_dashboard_router())
    router.include_router(make_portal_vehicles_router())
    router.include_router(make_portal_payouts_router())
    return router
