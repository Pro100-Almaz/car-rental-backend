from fastapi import APIRouter

from app.presentation.http.fines.charge_fine import make_charge_fine_router
from app.presentation.http.fines.create_fine import make_create_fine_router
from app.presentation.http.fines.get_fine import make_get_fine_router
from app.presentation.http.fines.list_fines import make_list_fines_router


def make_fines_router() -> APIRouter:
    router = APIRouter(
        prefix="/fines",
        tags=["Fines"],
    )
    router.include_router(make_create_fine_router())
    router.include_router(make_list_fines_router())
    router.include_router(make_get_fine_router())
    router.include_router(make_charge_fine_router())
    return router
