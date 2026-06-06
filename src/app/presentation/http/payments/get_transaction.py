from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import TransactionNotFoundError
from app.core.queries.get_transaction import GetTransaction, GetTransactionRequest
from app.core.queries.models.transaction import TransactionQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_transaction_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/transactions/{transaction_id}",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            TransactionNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "Transaction not found"}},
    )
    @inject
    async def get_transaction(
        transaction_id: UUID,
        interactor: FromDishka[GetTransaction],
    ) -> TransactionQm:
        result = await interactor.execute(GetTransactionRequest(transaction_id=transaction_id))
        if result is None:
            raise TransactionNotFoundError
        return result

    return router
