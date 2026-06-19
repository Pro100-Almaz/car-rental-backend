import logging

from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.queries.models.user import UserQm
from app.core.queries.ports.user_reader import UserReader

logger = logging.getLogger(__name__)


class GetCurrentUser:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_reader: UserReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._user_reader = user_reader

    async def execute(self) -> UserQm:
        logger.info("Get current user: started.")
        current_user = await self._current_user_service.get_current_user()
        res = self._user_reader.row_to_qm(current_user)
        logger.info("Get current user: done.")

        if res is None:
            raise Exception("User not found")

        return res
