from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_organization import GetOrganization, GetOrganizationRequest
from app.core.queries.models.organization import OrganizationQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_organization_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{organization_id}",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_organization(
        organization_id: UUID,
        interactor: FromDishka[GetOrganization] = ...,  # type: ignore[assignment]
    ) -> OrganizationQm:
        result = await interactor.execute(GetOrganizationRequest(organization_id=organization_id))
        if result is None:
            return JSONResponse(status_code=404, content={"detail": "Organization not found"})  # type: ignore[return-value]
        return result

    return router
