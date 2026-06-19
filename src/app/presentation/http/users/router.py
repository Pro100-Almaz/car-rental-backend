from fastapi import APIRouter

from app.presentation.http.users.activate_user import make_activate_user_router
from app.presentation.http.users.create_user import make_create_user_router
from app.presentation.http.users.deactivate_user import make_deactivate_user_router
from app.presentation.http.users.get_curr_user import make_current_user_router
from app.presentation.http.users.list_users import make_list_users_router
from app.presentation.http.users.set_user_password import make_set_user_password_router
from app.presentation.http.users.set_user_role import make_set_user_role_router


def make_users_router() -> APIRouter:
    router = APIRouter(
        prefix="/users",
        tags=["Users"],
    )
    router.include_router(make_create_user_router())
    router.include_router(make_list_users_router())
    router.include_router(make_set_user_password_router())
    router.include_router(make_set_user_role_router())
    router.include_router(make_activate_user_router())
    router.include_router(make_deactivate_user_router())
    router.include_router(make_current_user_router())
    return router
