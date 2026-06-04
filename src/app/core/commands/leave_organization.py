import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import (
    CannotLeaveHomeOrganizationError,
    ClientNotFoundError,
    ClientOrganizationNotFoundError,
)
from app.core.commands.ports.client_organization_tx_storage import ClientOrganizationTxStorage
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.client_reader import ClientReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class LeaveOrganizationRequest:
    organization_id: UUID


class LeaveOrganization:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_reader: ClientReader,
        client_org_tx_storage: ClientOrganizationTxStorage,
        transaction_manager: TransactionManager,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_reader
        self._client_org_tx_storage = client_org_tx_storage
        self._transaction_manager = transaction_manager

    async def execute(self, request: LeaveOrganizationRequest) -> None:
        logger.info("Leave organization: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.organizations.leave",
            ),
        )

        client = await self._client_reader.get_by_user_id(user_id=current_user.id_)
        if client is None:
            raise ClientNotFoundError

        if client.organization_id == request.organization_id:
            raise CannotLeaveHomeOrganizationError

        existing = await self._client_org_tx_storage.get_by_client_and_org(
            client_id=client.id,
            organization_id=request.organization_id,
        )
        if existing is None:
            raise ClientOrganizationNotFoundError

        await self._client_org_tx_storage.delete(existing)
        await self._transaction_manager.commit()

        logger.info("Leave organization: done.")
