from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel

from app.core.commands.exceptions import (
    AlreadyJoinedOrganizationError,
    ClientNotFoundError,
    OrganizationNotFoundError,
)
from app.core.commands.join_organization import JoinOrganization, JoinOrganizationRequest
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class JoinOrganizationBody(BaseModel):
    organization_id: UUID


def make_join_organization_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/organizations/join",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
            OrganizationNotFoundError: status.HTTP_404_NOT_FOUND,
            AlreadyJoinedOrganizationError: status.HTTP_409_CONFLICT,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def join_organization(
        body: JoinOrganizationBody,
        handler: FromDishka[JoinOrganization],
    ) -> None:
        await handler.execute(
            JoinOrganizationRequest(organization_id=body.organization_id)
        )

    return router
