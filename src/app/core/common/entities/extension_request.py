from datetime import datetime
from decimal import Decimal

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    ClientId,
    ExtensionRequestId,
    ExtensionRequestStatus,
    OrganizationId,
    RentalId,
    UserId,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class ExtensionRequest(Entity[ExtensionRequestId]):
    def __init__(
        self,
        *,
        id_: ExtensionRequestId,
        organization_id: OrganizationId,
        rental_id: RentalId,
        client_id: ClientId,
        new_end_date: UtcDatetime,
        additional_cost: Decimal,
        status: ExtensionRequestStatus,
        rejection_reason: str | None,
        reviewed_by: UserId | None,
        reviewed_at: datetime | None,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.rental_id = rental_id
        self.client_id = client_id
        self.new_end_date = new_end_date
        self.additional_cost = additional_cost
        self.status = status
        self.rejection_reason = rejection_reason
        self.reviewed_by = reviewed_by
        self.reviewed_at = reviewed_at
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
