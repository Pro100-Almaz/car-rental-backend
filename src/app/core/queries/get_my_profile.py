import logging

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.models.client import ClientQm
from app.core.queries.ports.client_reader import ClientReader

logger = logging.getLogger(__name__)


class GetMyProfile:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_reader: ClientReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_reader

    async def execute(self) -> ClientQm | None:
        logger.info("Get my profile: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.profile",
            ),
        )

        result = await self._client_reader.get_by_user_id(user_id=current_user.id_)

        logger.info("Get my profile: done.")
        return result
