import logging

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.models.mobile_rental import MobileRentalQm
from app.core.queries.ports.client_reader import ClientReader
from app.core.queries.ports.mobile_rental_reader import MobileRentalReader

logger = logging.getLogger(__name__)


class GetMyActiveRental:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_reader: ClientReader,
        mobile_rental_reader: MobileRentalReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_reader
        self._mobile_rental_reader = mobile_rental_reader

    async def execute(self) -> MobileRentalQm | None:
        logger.info("Get my active rental: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.rental",
            ),
        )

        client = await self._client_reader.get_by_user_id(user_id=current_user.id_)
        if client is None:
            return None

        result = await self._mobile_rental_reader.get_active_by_client(
            client_id=client.id,
        )

        logger.info("Get my active rental: done.")
        return result
