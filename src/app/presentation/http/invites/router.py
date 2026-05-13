from fastapi import APIRouter

from app.presentation.http.invites.create_invite import make_create_invite_router
from app.presentation.http.invites.get_invite import make_get_invite_router


def make_invites_router() -> APIRouter:
    router = APIRouter(prefix="/invites", tags=["Invites"])
    router.include_router(make_create_invite_router())
    router.include_router(make_get_invite_router())
    return router
