from fastapi import APIRouter

from app.presentation.http.payments.charge import make_charge_router
from app.presentation.http.payments.get_transaction import make_get_transaction_router
from app.presentation.http.payments.hold_deposit import make_hold_deposit_router
from app.presentation.http.payments.list_transactions import make_list_transactions_router
from app.presentation.http.payments.refund import make_refund_router
from app.presentation.http.payments.release_deposit import make_release_deposit_router
from app.presentation.http.payments.update_transaction_status import make_update_transaction_status_router


def make_payments_router() -> APIRouter:
    router = APIRouter(
        prefix="/payments",
        tags=["Payments"],
    )
    router.include_router(make_hold_deposit_router())
    router.include_router(make_release_deposit_router())
    router.include_router(make_charge_router())
    router.include_router(make_refund_router())
    router.include_router(make_list_transactions_router())
    router.include_router(make_get_transaction_router())
    router.include_router(make_update_transaction_status_router())
    return router
