import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.client import ClientQm
from app.core.queries.ports.client_reader import ClientReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetClientRequest:
    client_id: UUID


class GetClient:
    def __init__(
        self,
        client_reader: ClientReader,
    ) -> None:
        self._client_reader = client_reader

    async def execute(self, request: GetClientRequest) -> ClientQm | None:
        logger.info("Get client: started.")

        result = await self._client_reader.get_by_id(
            client_id=request.client_id,
        )

        logger.info("Get client: done.")
        return result
