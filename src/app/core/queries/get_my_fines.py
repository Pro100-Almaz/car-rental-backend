import logging

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.client_reader import ClientReader
from app.core.queries.ports.fine_reader import FineReader, ListFinesQm

logger = logging.getLogger(__name__)


class GetMyFines:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_reader: ClientReader,
        fine_reader: FineReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_reader
        self._fine_reader = fine_reader

    async def execute(self) -> ListFinesQm:
        logger.info("Get my fines: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.payments",
            ),
        )

        client = await self._client_reader.get_by_user_id(user_id=current_user.id_)
        if client is None:
            return ListFinesQm(fines=[], total=0)

        result = await self._fine_reader.list_fines(
            organization_id=client.organization_id,
            client_id=client.id,
        )

        logger.info("Get my fines: done.")
        return result
