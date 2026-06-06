from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from app.core.commands.exceptions import OrganizationNotFoundError
from app.core.commands.ports.organization_tx_storage import OrganizationTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.types_ import OrganizationId
from app.core.common.value_objects.utc_datetime import UtcDatetime

logger = logging.getLogger(__name__)

_UNSET = object()


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateOrganizationRequest:
    organization_id: UUID
    name: str | object = _UNSET
    settings: dict[str, Any] | object = _UNSET


class UpdateOrganization:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        utc_timer: UtcTimer,
        organization_tx_storage: OrganizationTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._utc_timer = utc_timer
        self._organization_tx_storage = organization_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateOrganizationRequest) -> None:
        logger.info("Update organization: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="organization.update",
            ),
        )

        organization_id = OrganizationId(request.organization_id)
        organization = await self._organization_tx_storage.get_by_id(organization_id, for_update=True)
        if organization is None:
            raise OrganizationNotFoundError

        changed = False

        if request.name is not _UNSET and request.name != organization.name:
            organization.name = request.name  # type: ignore[assignment]
            changed = True

        if request.settings is not _UNSET:
            current_settings = organization.settings or {}
            merged = {**current_settings, **cast(dict[str, Any], request.settings)}
            if merged != current_settings:
                organization.settings = merged
                changed = True

        if changed:
            organization.updated_at = UtcDatetime(self._utc_timer.now.value)
            await self._transaction_manager.commit()

        logger.info("Update organization: done.")
