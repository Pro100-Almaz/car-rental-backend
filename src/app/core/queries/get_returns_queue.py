import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.queries.models.returns_queue import ReturnsQueueQm
from app.core.queries.ports.returns_queue_reader import ReturnsQueueReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetReturnsQueueRequest:
    organization_id: UUID
    now: datetime
    horizon: datetime


class GetReturnsQueue:
    def __init__(
        self,
        returns_queue_reader: ReturnsQueueReader,
    ) -> None:
        self._reader = returns_queue_reader

    async def execute(self, request: GetReturnsQueueRequest) -> ReturnsQueueQm:
        logger.info("Get returns queue: started.")

        result = await self._reader.get_returns_queue(
            organization_id=request.organization_id,
            now=request.now,
            horizon=request.horizon,
        )

        logger.info("Get returns queue: done.")
        return result
