import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.fine import FineQm
from app.core.queries.ports.fine_reader import FineReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetFineRequest:
    fine_id: UUID


class GetFine:
    def __init__(
        self,
        fine_reader: FineReader,
    ) -> None:
        self._fine_reader = fine_reader

    async def execute(self, request: GetFineRequest) -> FineQm | None:
        logger.info("Get fine: started.")

        result = await self._fine_reader.get_by_id(
            fine_id=request.fine_id,
        )

        logger.info("Get fine: done.")
        return result
