from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, status
from fastapi_error_map import ErrorAwareRouter

from app.core.queries.get_fine import GetFine, GetFineRequest
from app.core.queries.models.fine import FineQm
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


def make_get_fine_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/{fine_id}",
        error_map={
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        responses={404: {"description": "Fine not found"}},
    )
    @inject
    async def get_fine(
        fine_id: UUID,
        interactor: FromDishka[GetFine],
    ) -> FineQm:
        result = await interactor.execute(GetFineRequest(fine_id=fine_id))
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fine not found.")
        return result

    return router
