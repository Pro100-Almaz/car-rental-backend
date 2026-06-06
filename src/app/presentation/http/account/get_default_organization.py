from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.infrastructure.auth_ctx.verification_types import DefaultOrganizationId
from app.presentation.http.errors.callbacks import log_info


class DefaultOrganizationResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    organization_id: UUID | None


def make_get_default_organization_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/default-organization/",
        error_map={},
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        description=(
            "Return the platform's configured default organization id, or null if none is set. "
            "Used by signup UIs to decide whether to ask the user to pick an organization."
        ),
    )
    @inject
    async def get_default_organization(
        default_organization_id: FromDishka[DefaultOrganizationId],
    ) -> DefaultOrganizationResponse:
        return DefaultOrganizationResponse(organization_id=default_organization_id)

    return router
