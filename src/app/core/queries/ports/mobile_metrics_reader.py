from typing import Protocol
from uuid import UUID

from app.core.queries.models.mobile_metrics import MobileMetricsQm


class MobileMetricsReader(Protocol):
    async def get_metrics(
        self,
        *,
        organization_id: UUID,
    ) -> MobileMetricsQm: ...
