from decimal import Decimal

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import BranchId, OrganizationId
from app.core.common.value_objects.utc_datetime import UtcDatetime


class Branch(Entity[BranchId]):
    def __init__(
        self,
        *,
        id_: BranchId,
        organization_id: OrganizationId,
        name: str,
        address: str,
        latitude: Decimal | None,
        longitude: Decimal | None,
        timezone: str,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.name = name
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
