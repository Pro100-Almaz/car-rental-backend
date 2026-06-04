import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.queries.models.organization import OrganizationQm
from app.core.queries.ports.organization_reader import OrganizationReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetOrganizationRequest:
    organization_id: UUID


class GetOrganization:
    def __init__(self, organization_reader: OrganizationReader) -> None:
        self._organization_reader = organization_reader

    async def execute(self, request: GetOrganizationRequest) -> OrganizationQm | None:
        logger.info("Get organization: started.")
        result = await self._organization_reader.get_by_id(
            organization_id=request.organization_id,
        )
        logger.info("Get organization: done.")
        return result
