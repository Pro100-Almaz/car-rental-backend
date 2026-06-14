"""Internal job router — server-to-server endpoints excluded from public OpenAPI."""

from fastapi import APIRouter

from app.presentation.http.internal.check_overdue_rentals import make_check_overdue_rentals_router
from app.presentation.http.internal.check_pickup_reminders import make_check_pickup_reminders_router
from app.presentation.http.internal.check_return_reminders import make_check_return_reminders_router


def make_internal_router() -> APIRouter:
    router = APIRouter(
        prefix="/internal/jobs",
        tags=["Internal"],
        include_in_schema=False,
    )
    router.include_router(make_check_overdue_rentals_router())
    router.include_router(make_check_pickup_reminders_router())
    router.include_router(make_check_return_reminders_router())
    return router
