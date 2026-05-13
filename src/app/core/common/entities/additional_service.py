from decimal import Decimal

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import AdditionalServiceId, OrganizationId
from app.core.common.value_objects.utc_datetime import UtcDatetime


class AdditionalService(Entity[AdditionalServiceId]):
    def __init__(
        self,
        *,
        id_: AdditionalServiceId,
        organization_id: OrganizationId,
        name: str,
        price: Decimal,
        is_active: bool,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.name = name
        self.price = price
        self.is_active = is_active
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
