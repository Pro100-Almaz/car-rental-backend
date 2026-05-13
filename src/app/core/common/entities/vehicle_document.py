from datetime import date

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import VehicleDocumentId, VehicleId
from app.core.common.value_objects.utc_datetime import UtcDatetime


class VehicleDocument(Entity[VehicleDocumentId]):
    def __init__(
        self,
        *,
        id_: VehicleDocumentId,
        vehicle_id: VehicleId,
        document_type: str,
        name: str,
        url: str,
        expiry_date: date | None,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.vehicle_id = vehicle_id
        self.document_type = document_type
        self.name = name
        self.url = url
        self.expiry_date = expiry_date
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
