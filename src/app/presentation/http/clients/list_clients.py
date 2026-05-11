from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.queries.list_clients import ListClients, ListClientsRequest
from app.core.queries.ports.client_reader import ListClientsQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ListClientsRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_id: UUID
    verification_status: str | None = None
    is_blacklisted: bool | None = None


def make_list_clients_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_clients(
        request_schema: Annotated[ListClientsRequestSchema, Depends()],
        interactor: FromDishka[ListClients],
    ) -> ListClientsQm:
        request = ListClientsRequest(
            organization_id=request_schema.organization_id,
            verification_status=request_schema.verification_status,
            is_blacklisted=request_schema.is_blacklisted,
        )
        return await interactor.execute(request)

    return router
