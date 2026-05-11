from fastapi import APIRouter, Depends
from fastapi.security import APIKeyCookie

from app.presentation.http.users.activate_user import make_activate_user_router
from app.presentation.http.users.create_user import make_create_user_router
from app.presentation.http.users.deactivate_user import make_deactivate_user_router
from app.presentation.http.users.list_users import make_list_users_router
from app.presentation.http.users.set_user_password import make_set_user_password_router
from app.presentation.http.users.set_user_role import make_set_user_role_router


def make_users_router(*, cookie_name: str) -> APIRouter:
    router = APIRouter(
        prefix="/users",
        tags=["Users"],
        dependencies=[Depends(APIKeyCookie(name=cookie_name))],
    )
    router.include_router(make_create_user_router())
    router.include_router(make_list_users_router())
    router.include_router(make_set_user_password_router())
    router.include_router(make_set_user_role_router())
    router.include_router(make_activate_user_router())
    router.include_router(make_deactivate_user_router())
    return router
