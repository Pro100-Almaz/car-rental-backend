from fastapi import APIRouter

from app.presentation.http.dashboard.active_rentals import make_active_rentals_router
from app.presentation.http.dashboard.alerts import make_alerts_router
from app.presentation.http.dashboard.kpis import make_kpis_router
from app.presentation.http.dashboard.mobile_metrics import make_mobile_metrics_router
from app.presentation.http.dashboard.revenue_chart import make_revenue_chart_router


def make_dashboard_router() -> APIRouter:
    router = APIRouter(
        prefix="/dashboard",
        tags=["Dashboard"],
    )
    router.include_router(make_kpis_router())
    router.include_router(make_alerts_router())
    router.include_router(make_active_rentals_router())
    router.include_router(make_revenue_chart_router())
    router.include_router(make_mobile_metrics_router())
    return router
