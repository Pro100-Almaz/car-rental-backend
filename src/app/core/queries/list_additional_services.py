import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.ports.additional_service_reader import AdditionalServiceReader, ListAdditionalServicesQm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListAdditionalServicesRequest:
    organization_id: UUID
    is_active: bool | None = None


class ListAdditionalServices:
    def __init__(
        self,
        additional_service_reader: AdditionalServiceReader,
    ) -> None:
        self._additional_service_reader = additional_service_reader

    async def execute(self, request: ListAdditionalServicesRequest) -> ListAdditionalServicesQm:
        logger.info("List additional services: started.")

        result = await self._additional_service_reader.list_additional_services(
            organization_id=request.organization_id,
            is_active=request.is_active,
        )

        logger.info("List additional services: done.")
        return result
