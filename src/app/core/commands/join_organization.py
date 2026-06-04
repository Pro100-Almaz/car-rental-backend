import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.commands.exceptions import (
    AlreadyJoinedOrganizationError,
    ClientNotFoundError,
    OrganizationNotFoundError,
)
from app.core.commands.ports.client_organization_tx_storage import ClientOrganizationTxStorage
from app.core.commands.ports.flusher import Flusher
from app.core.commands.ports.transaction_manager import TransactionManager
from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.common.entities.client_organization import ClientOrganization
from app.core.common.entities.types_ import ClientId, OrganizationId
from app.core.common.factories.id_factory import create_client_organization_id
from app.core.queries.ports.client_reader import ClientReader
from app.core.queries.ports.organization_reader import OrganizationReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class JoinOrganizationRequest:
    organization_id: UUID


class JoinOrganization:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_reader: ClientReader,
        organization_reader: OrganizationReader,
        client_org_tx_storage: ClientOrganizationTxStorage,
        flusher: Flusher,
        transaction_manager: TransactionManager,
        utc_timer: UtcTimer,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_reader
        self._organization_reader = organization_reader
        self._client_org_tx_storage = client_org_tx_storage
        self._flusher = flusher
        self._transaction_manager = transaction_manager
        self._utc_timer = utc_timer

    async def execute(self, request: JoinOrganizationRequest) -> None:
        logger.info("Join organization: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.organizations.join",
            ),
        )

        client = await self._client_reader.get_by_user_id(user_id=current_user.id_)
        if client is None:
            raise ClientNotFoundError

        org = await self._organization_reader.get_by_id(
            organization_id=request.organization_id,
        )
        if org is None:
            raise OrganizationNotFoundError

        existing = await self._client_org_tx_storage.get_by_client_and_org(
            client_id=client.id,
            organization_id=request.organization_id,
        )
        if existing is not None:
            raise AlreadyJoinedOrganizationError

        now = self._utc_timer.now
        client_org = ClientOrganization(
            id_=create_client_organization_id(),
            client_id=ClientId(client.id),
            organization_id=OrganizationId(request.organization_id),
            joined_at=now,
        )
        self._client_org_tx_storage.add(client_org)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        logger.info("Join organization: done.")
