from fastapi import APIRouter

from app.presentation.http.clients.blacklist_client import make_blacklist_client_router
from app.presentation.http.clients.create_client import make_create_client_router
from app.presentation.http.clients.get_client import make_get_client_router
from app.presentation.http.clients.list_clients import make_list_clients_router
from app.presentation.http.clients.update_client import make_update_client_router
from app.presentation.http.clients.verify_client import make_verify_client_router


def make_clients_router() -> APIRouter:
    router = APIRouter(
        prefix="/clients",
        tags=["Clients"],
    )
    router.include_router(make_create_client_router())
    router.include_router(make_list_clients_router())
    router.include_router(make_get_client_router())
    router.include_router(make_update_client_router())
    router.include_router(make_verify_client_router())
    router.include_router(make_blacklist_client_router())
    return router
