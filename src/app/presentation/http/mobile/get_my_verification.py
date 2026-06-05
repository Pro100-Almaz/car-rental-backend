from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status
from fastapi_error_map import ErrorAwareRouter

from app.core.common.authorization.exceptions import AuthorizationError
from app.core.queries.get_my_verification import GetMyVerification, VerificationStatusQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_my_verification_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/clients/me/verification",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "Client not found"}},
    )
    @inject
    async def get_my_verification(
        interactor: FromDishka[GetMyVerification],
    ) -> VerificationStatusQm:
        result = await interactor.execute()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found.",
            )
        return result

    return router
