from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_investor import GetInvestor, GetInvestorRequest
from app.core.queries.models.investor import InvestorQm
from app.infrastructure.exceptions import StorageError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_investor_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{investor_id}",
        error_map={
            StorageError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "Investor not found"}},
    )
    @inject
    async def get_investor(
        investor_id: UUID,
        interactor: FromDishka[GetInvestor],
    ) -> InvestorQm:
        result = await interactor.execute(GetInvestorRequest(investor_id=investor_id))
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investor not found.")
        return result

    return router
