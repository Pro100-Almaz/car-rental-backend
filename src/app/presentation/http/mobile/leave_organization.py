from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import (
    CannotLeaveHomeOrganizationError,
    ClientNotFoundError,
    ClientOrganizationNotFoundError,
)
from app.core.commands.leave_organization import LeaveOrganization, LeaveOrganizationRequest
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_leave_organization_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.delete(
        "/organizations/{organization_id}",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ClientNotFoundError: status.HTTP_404_NOT_FOUND,
            ClientOrganizationNotFoundError: status.HTTP_404_NOT_FOUND,
            CannotLeaveHomeOrganizationError: status.HTTP_400_BAD_REQUEST,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def leave_organization(
        organization_id: UUID,
        handler: FromDishka[LeaveOrganization],
    ) -> None:
        await handler.execute(LeaveOrganizationRequest(organization_id=organization_id))

    return router
