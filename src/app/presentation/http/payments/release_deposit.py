from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.release_deposit import ReleaseDeposit, ReleaseDepositRequest, ReleaseDepositResponse
from app.core.common.exceptions import BusinessTypeError
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_release_deposit_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.post(
        "/deposit/release",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            BusinessTypeError: status.HTTP_400_BAD_REQUEST,
        },
        default_on_error=log_info,
        status_code=status.HTTP_201_CREATED,
    )
    @inject
    async def release_deposit(
        request: ReleaseDepositRequest,
        interactor: FromDishka[ReleaseDeposit],
    ) -> ReleaseDepositResponse:
        return await interactor.execute(request)

    return router
