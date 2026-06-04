from typing import Protocol
from uuid import UUID

from app.core.queries.models.extension_request import ListExtensionRequestsQm


class ExtensionRequestReader(Protocol):
    async def list_pending(
        self,
        *,
        organization_id: UUID,
    ) -> ListExtensionRequestsQm: ...

    async def count_pending(
        self,
        *,
        organization_id: UUID,
    ) -> int: ...
