from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    InvestorId,
    InvestorType,
    OrganizationId,
    UserId,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class Investor(Entity[InvestorId]):
    def __init__(
        self,
        *,
        id_: InvestorId,
        organization_id: OrganizationId,
        full_name: str,
        type_: InvestorType,
        contact_phone: str | None,
        contact_email: str | None,
        user_id: UserId | None,
        notes: str | None,
        created_at: UtcDatetime,
        updated_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.full_name = full_name
        self.type_ = type_
        self.contact_phone = contact_phone
        self.contact_email = contact_email
        self.user_id = user_id
        self.notes = notes
        self._created_at = created_at
        self.updated_at = updated_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
