from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.list_transactions import ListTransactions, ListTransactionsRequest
from app.core.queries.ports.transaction_reader import ListTransactionsQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_client_payments_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{client_id}/payments",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_client_payments(
        client_id: UUID,
        organization_id: UUID = Query(...),
        interactor: FromDishka[ListTransactions] = ...,
    ) -> ListTransactionsQm:
        request = ListTransactionsRequest(
            organization_id=organization_id,
            client_id=client_id,
        )
        return await interactor.execute(request)

    return router
