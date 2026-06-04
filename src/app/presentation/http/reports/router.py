from fastapi import APIRouter

from app.presentation.http.reports.cash_flow import make_cash_flow_router
from app.presentation.http.reports.export import make_export_router
from app.presentation.http.reports.pnl import make_pnl_router
from app.presentation.http.reports.vehicles_comparison import make_vehicles_comparison_router


def make_reports_router() -> APIRouter:
    router = APIRouter(
        prefix="/reports",
        tags=["Reports"],
    )
    router.include_router(make_pnl_router())
    router.include_router(make_cash_flow_router())
    router.include_router(make_vehicles_comparison_router())
    router.include_router(make_export_router())
    return router
