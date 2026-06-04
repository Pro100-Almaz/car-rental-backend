from typing import Protocol
from uuid import UUID

from app.core.common.entities.client_organization import ClientOrganization


class ClientOrganizationTxStorage(Protocol):
    def add(self, client_organization: ClientOrganization) -> None: ...

    async def get_by_client_and_org(
        self,
        *,
        client_id: UUID,
        organization_id: UUID,
    ) -> ClientOrganization | None: ...

    async def delete(self, client_organization: ClientOrganization) -> None: ...
