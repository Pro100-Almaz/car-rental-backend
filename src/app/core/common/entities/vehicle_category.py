from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import OrganizationId, VehicleCategoryId
from app.core.common.value_objects.utc_datetime import UtcDatetime


class VehicleCategoryEntity(Entity[VehicleCategoryId]):
    def __init__(
        self,
        *,
        id_: VehicleCategoryId,
        organization_id: OrganizationId,
        name: str,
        sort_order: int,
        is_active: bool,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.name = name
        self.sort_order = sort_order
        self.is_active = is_active
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
