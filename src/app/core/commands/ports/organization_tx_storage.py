from abc import abstractmethod
from typing import Protocol

from app.core.common.entities.organization import Organization
from app.core.common.entities.types_ import OrganizationId


class OrganizationTxStorage(Protocol):
    @abstractmethod
    def add(self, organization: Organization) -> None: ...

    @abstractmethod
    async def get_by_id(
        self,
        organization_id: OrganizationId,
        *,
        for_update: bool = False,
    ) -> Organization | None: ...
