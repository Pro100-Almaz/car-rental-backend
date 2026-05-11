from datetime import date
from decimal import Decimal

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    ClientId,
    FineId,
    FineStatus,
    FineType,
    OrganizationId,
    RentalId,
    VehicleId,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class Fine(Entity[FineId]):
    def __init__(
        self,
        *,
        id_: FineId,
        organization_id: OrganizationId,
        vehicle_id: VehicleId,
        rental_id: RentalId | None,
        client_id: ClientId | None,
        fine_type: FineType,
        amount: Decimal,
        description: str | None,
        fine_date: date,
        document_url: str | None,
        status: FineStatus,
        created_at: UtcDatetime,
        updated_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.vehicle_id = vehicle_id
        self.rental_id = rental_id
        self.client_id = client_id
        self.fine_type = fine_type
        self.amount = amount
        self.description = description
        self.fine_date = fine_date
        self.document_url = document_url
        self.status = status
        self._created_at = created_at
        self.updated_at = updated_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
