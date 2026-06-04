import logging

from app.core.commands.exceptions import ClientNotFoundError
from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.client_organization_reader import ClientOrganizationReader, ListClientOrganizationsQm
from app.core.queries.ports.client_reader import ClientReader

logger = logging.getLogger(__name__)


class ListMyOrganizations:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_reader: ClientReader,
        client_org_reader: ClientOrganizationReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_reader
        self._client_org_reader = client_org_reader

    async def execute(self) -> ListClientOrganizationsQm:
        logger.info("List my organizations: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.organizations.list",
            ),
        )

        client = await self._client_reader.get_by_user_id(user_id=current_user.id_)
        if client is None:
            raise ClientNotFoundError

        result = await self._client_org_reader.list_by_client_id(client_id=client.id)

        logger.info("List my organizations: done.")
        return result
