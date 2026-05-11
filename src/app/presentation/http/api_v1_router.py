from fastapi import APIRouter

from app.presentation.http.account.router import make_account_router
from app.presentation.http.branches.router import make_branches_router
from app.presentation.http.clients.router import make_clients_router
from app.presentation.http.fines.router import make_fines_router
from app.presentation.http.organizations.router import make_organizations_router
from app.presentation.http.payments.router import make_payments_router
from app.presentation.http.rentals.router import make_rentals_router
from app.presentation.http.service_tasks.router import make_service_tasks_router
from app.presentation.http.users.router import make_users_router
from app.presentation.http.vehicles.router import make_vehicles_router


def make_v1_router(*, cookie_name: str) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(make_account_router(cookie_name=cookie_name))
    router.include_router(make_users_router(cookie_name=cookie_name))
    router.include_router(make_organizations_router())
    router.include_router(make_branches_router())
    router.include_router(make_vehicles_router())
    router.include_router(make_clients_router())
    router.include_router(make_rentals_router())
    router.include_router(make_payments_router())
    router.include_router(make_fines_router())
    router.include_router(make_service_tasks_router())
    return router
