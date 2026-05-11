import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.client_reader import ClientReader, ListClientsQm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListClientsRequest:
    organization_id: UUID
    verification_status: str | None = None
    is_blacklisted: bool | None = None


class ListClients:
    def __init__(
        self,
        client_reader: ClientReader,
    ) -> None:
        self._client_reader = client_reader

    async def execute(self, request: ListClientsRequest) -> ListClientsQm:
        logger.info("List clients: started.")

        result = await self._client_reader.list_clients(
            organization_id=request.organization_id,
            verification_status=request.verification_status,
            is_blacklisted=request.is_blacklisted,
        )

        logger.info("List clients: done.")
        return result
