from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.queries.list_transactions import ListTransactions, ListTransactionsRequest
from app.core.queries.ports.transaction_reader import ListTransactionsQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ListTransactionsRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_id: UUID
    rental_id: UUID | None = None
    client_id: UUID | None = None
    type_: str | None = None
    status: str | None = None


def make_list_transactions_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/transactions",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_transactions(
        request_schema: Annotated[ListTransactionsRequestSchema, Depends()],
        interactor: FromDishka[ListTransactions],
    ) -> ListTransactionsQm:
        request = ListTransactionsRequest(
            organization_id=request_schema.organization_id,
            rental_id=request_schema.rental_id,
            client_id=request_schema.client_id,
            type_=request_schema.type_,
            status=request_schema.status,
        )
        return await interactor.execute(request)

    return router
