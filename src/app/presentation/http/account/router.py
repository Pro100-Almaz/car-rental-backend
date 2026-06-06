from fastapi import APIRouter

from app.presentation.http.account.change_password import make_change_password_router
from app.presentation.http.account.forgot_password import make_forgot_password_router
from app.presentation.http.account.get_default_organization import make_get_default_organization_router
from app.presentation.http.account.log_in import make_log_in_router
from app.presentation.http.account.log_out import make_log_out_router
from app.presentation.http.account.log_out_all import make_log_out_all_router
from app.presentation.http.account.refresh import make_refresh_router
from app.presentation.http.account.resend_verification import make_resend_verification_router
from app.presentation.http.account.reset_password import make_reset_password_router
from app.presentation.http.account.sign_up import make_sign_up_router
from app.presentation.http.account.verify_email import make_verify_email_router


def make_account_router() -> APIRouter:
    router = APIRouter(prefix="/account", tags=["Account"])
    router.include_router(make_sign_up_router())
    router.include_router(make_log_in_router())
    router.include_router(make_verify_email_router())
    router.include_router(make_resend_verification_router())
    router.include_router(make_change_password_router())
    router.include_router(make_forgot_password_router())
    router.include_router(make_reset_password_router())
    router.include_router(make_log_out_router())
    router.include_router(make_log_out_all_router())
    router.include_router(make_refresh_router())
    router.include_router(make_get_default_organization_router())
    return router
