from abc import abstractmethod
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.core.queries.models.returns_queue import ReturnsQueueQm


class ReturnsQueueReader(Protocol):
    @abstractmethod
    async def get_returns_queue(
        self,
        *,
        organization_id: UUID,
        now: datetime,
        horizon: datetime,
    ) -> ReturnsQueueQm: ...
