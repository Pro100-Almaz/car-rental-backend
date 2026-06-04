from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    ClientId,
    ClientOrganizationId,
    OrganizationId,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class ClientOrganization(Entity[ClientOrganizationId]):
    def __init__(
        self,
        *,
        id_: ClientOrganizationId,
        client_id: ClientId,
        organization_id: OrganizationId,
        joined_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.client_id = client_id
        self.organization_id = organization_id
        self._joined_at = joined_at

    @property
    def joined_at(self) -> UtcDatetime:
        return self._joined_at
