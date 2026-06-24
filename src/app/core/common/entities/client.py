from decimal import Decimal
from typing import Any

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    ClientId,
    OrganizationId,
    RegistrationSource,
    TrustLevel,
    UserId,
    VerificationStatus,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class Client(Entity[ClientId]):
    def __init__(
        self,
        *,
        id_: ClientId,
        organization_id: OrganizationId,
        user_id: UserId | None,
        phone: str,
        email: str | None,
        first_name: str,
        last_name: str,
        verification_status: VerificationStatus,
        trust_score: int,
        trust_level: TrustLevel,
        is_blacklisted: bool,
        blacklist_reason: str | None,
        wallet_balance: Decimal,
        debt_balance: Decimal,
        registration_source: RegistrationSource,
        rejection_reason: str | None,
        metadata: dict[str, Any] | None,
        created_at: UtcDatetime,
        updated_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.user_id = user_id
        self.phone = phone
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.verification_status = verification_status
        self.trust_score = trust_score
        self.trust_level = trust_level
        self.is_blacklisted = is_blacklisted
        self.blacklist_reason = blacklist_reason
        self.wallet_balance = wallet_balance
        self.debt_balance = debt_balance
        self.registration_source = registration_source
        self.rejection_reason = rejection_reason
        self.metadata = metadata
        self._created_at = created_at
        self.updated_at = updated_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
