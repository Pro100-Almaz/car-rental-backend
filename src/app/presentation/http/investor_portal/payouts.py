from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi_error_map import ErrorAwareRouter

from app.core.commands.exceptions import InvestorNotFoundError
from app.core.queries.investor_portal_payouts import InvestorPortalPayouts
from app.core.queries.ports.investor_reader import ListInvestorPayoutsQm
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_portal_payouts_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/payouts",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
            InvestorNotFoundError: status.HTTP_404_NOT_FOUND,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def portal_payouts(
        interactor: FromDishka[InvestorPortalPayouts] = ...,  # type: ignore[assignment]
    ) -> ListInvestorPayoutsQm:
        return await interactor.execute()

    return router
