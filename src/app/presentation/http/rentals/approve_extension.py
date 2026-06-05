from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.approve_extension_request import ApproveExtensionRequest, ApproveExtensionRequestInput
from app.core.commands.exceptions import ExtensionRequestNotFoundError, InvalidExtensionRequestStatusError
from app.core.common.authorization.exceptions import AuthorizationError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_approve_extension_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/{rental_id}/extension/approve",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ExtensionRequestNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidExtensionRequestStatusError: status.HTTP_409_CONFLICT,
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def approve_extension(
        rental_id: UUID,
        interactor: FromDishka[ApproveExtensionRequest],
    ) -> None:
        return await interactor.execute(ApproveExtensionRequestInput(extension_request_id=rental_id))

    return router
