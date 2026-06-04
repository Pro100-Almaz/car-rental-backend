from typing import Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.commands.exceptions import OrganizationNotFoundError
from app.core.commands.update_organization import UpdateOrganization, UpdateOrganizationRequest
from app.infrastructure.exceptions import StorageError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class UpdateOrganizationBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str | None = None
    settings: dict[str, Any] | None = None


def make_update_organization_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.patch(
        "/{organization_id}",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            OrganizationNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def update_organization(
        organization_id: UUID,
        body: UpdateOrganizationBody,
        interactor: FromDishka[UpdateOrganization],
    ) -> None:
        fields_set = body.model_fields_set
        kwargs: dict[str, Any] = {"organization_id": organization_id}
        for field_name in UpdateOrganizationBody.model_fields:
            if field_name in fields_set:
                kwargs[field_name] = getattr(body, field_name)
        request = UpdateOrganizationRequest(**kwargs)
        await interactor.execute(request)

    return router
