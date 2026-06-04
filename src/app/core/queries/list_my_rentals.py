import logging
from dataclasses import dataclass

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.client_reader import ClientReader
from app.core.queries.ports.mobile_rental_reader import ListMobileRentalsQm, MobileRentalReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListMyRentalsRequest:
    status: str | None = None


class ListMyRentals:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_reader: ClientReader,
        mobile_rental_reader: MobileRentalReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_reader
        self._mobile_rental_reader = mobile_rental_reader

    async def execute(self, request: ListMyRentalsRequest) -> ListMobileRentalsQm:
        logger.info("List my rentals: started.")

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
            return ListMobileRentalsQm(rentals=[], total=0)

        result = await self._mobile_rental_reader.list_by_client(
            client_id=client.id,
            status=request.status,
        )

        logger.info("List my rentals: done.")
        return result
