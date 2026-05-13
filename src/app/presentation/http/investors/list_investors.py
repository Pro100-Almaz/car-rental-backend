from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.list_investors import ListInvestors, ListInvestorsRequest
from app.core.queries.ports.investor_reader import ListInvestorsQm
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_investors_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def list_investors(
        organization_id: Annotated[UUID, Query(...)],
        type_: Annotated[str | None, Query(alias="type")] = None,
        interactor: FromDishka[ListInvestors] = ...,  # type: ignore[assignment]
    ) -> ListInvestorsQm:
        request = ListInvestorsRequest(
            organization_id=organization_id,
            type_=type_,
        )
        return await interactor.execute(request)

    return router
