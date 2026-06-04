from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.get_my_payments import GetMyPayments, GetMyPaymentsRequest
from app.core.queries.ports.transaction_reader import ListTransactionsQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_my_payments_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/clients/me/payments",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_my_payments(
        interactor: FromDishka[GetMyPayments],
        payment_status: str | None = Query(None, alias="status"),
        type_: str | None = Query(None, alias="type"),
    ) -> ListTransactionsQm:
        return await interactor.execute(
            GetMyPaymentsRequest(status=payment_status, type_=type_)
        )

    return router
