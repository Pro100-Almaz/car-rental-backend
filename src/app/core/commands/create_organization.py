import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypedDict
from uuid import UUID

from app.core.commands.exceptions import OrganizationSlugAlreadyExistsError
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.organization_tx_storage import OrganizationTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.entities.organization import Organization
from app.core.common.factories.id_factory import create_organization_id
from app.core.common.value_objects.slug import Slug
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateOrganizationRequest:
    name: str
    slug: str
    subscription_plan: str
    settings: dict[str, Any] | None = None


class CreateOrganizationResponse(TypedDict):
    id: UUID
    created_at: datetime


class CreateOrganization:
    def __init__(
        self,
        utc_timer: UtcTimer,
        organization_tx_storage: OrganizationTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._utc_timer = utc_timer
        self._organization_tx_storage = organization_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateOrganizationRequest) -> CreateOrganizationResponse:
        logger.info("Create organization: started.")

        slug = Slug(request.slug)
        now = UtcDatetime(self._utc_timer.now.value)

        organization = Organization(
            id_=create_organization_id(),
            name=request.name,
            slug=slug,
            settings=request.settings,
            subscription_plan=request.subscription_plan,
            created_at=now,
            updated_at=now,
        )
        self._organization_tx_storage.add(organization)
        try:
            await self._flusher.flush()
        except OrganizationSlugAlreadyExistsError:
            raise

        await self._transaction_manager.commit()

        logger.info("Create organization: done.")
        return CreateOrganizationResponse(
            id=organization.id_,
            created_at=organization.created_at.value,
        )
