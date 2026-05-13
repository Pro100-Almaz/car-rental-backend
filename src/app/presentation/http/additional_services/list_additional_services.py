from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.list_additional_services import ListAdditionalServices, ListAdditionalServicesRequest
from app.core.queries.ports.additional_service_reader import ListAdditionalServicesQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_list_additional_services_router() -> APIRouter:
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
    async def list_additional_services(
        organization_id: Annotated[UUID, Query(...)],
        is_active: Annotated[bool | None, Query()] = None,
        interactor: FromDishka[ListAdditionalServices] = ...,  # type: ignore[assignment]
    ) -> ListAdditionalServicesQm:
        request = ListAdditionalServicesRequest(
            organization_id=organization_id,
            is_active=is_active,
        )
        return await interactor.execute(request)

    return router
