from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter
from pydantic import BaseModel, ConfigDict

from app.core.queries.get_returns_queue import GetReturnsQueue, GetReturnsQueueRequest
from app.core.queries.models.returns_queue import ReturnsQueueQm
from app.infrastructure.auth_ctx.exceptions import AuthenticationError
from app.infrastructure.exceptions import ReaderError
from app.presentation.http.errors.callbacks import log_info
from app.presentation.http.errors.rules import HTTP_503_SERVICE_UNAVAILABLE_RULE


class ReturnsQueueRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    organization_id: UUID


def make_get_returns_queue_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/returns-queue",
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ReaderError: HTTP_503_SERVICE_UNAVAILABLE_RULE,
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_returns_queue(
        request_schema: Annotated[ReturnsQueueRequestSchema, Depends()],
        interactor: FromDishka[GetReturnsQueue],
    ) -> ReturnsQueueQm:
        now = datetime.now(tz=UTC)
        tomorrow_end = (now + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
        request = GetReturnsQueueRequest(
            organization_id=request_schema.organization_id,
            now=now,
            horizon=tomorrow_end,
        )
        return await interactor.execute(request)

    return router
