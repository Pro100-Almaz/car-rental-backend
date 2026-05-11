from typing import Any

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import OrganizationId
from app.core.common.value_objects.slug import Slug
from app.core.common.value_objects.utc_datetime import UtcDatetime


class Organization(Entity[OrganizationId]):
    def __init__(
        self,
        *,
        id_: OrganizationId,
        name: str,
        slug: Slug,
        settings: dict[str, Any] | None,
        subscription_plan: str,
        created_at: UtcDatetime,
        updated_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.name = name
        self.slug = slug
        self.settings = settings
        self.subscription_plan = subscription_plan
        self._created_at = created_at
        self.updated_at = updated_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
