import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.rental_reader import ListRentalsQm, RentalReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListBookingRequestsRequest:
    organization_id: UUID


class ListBookingRequests:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        rental_reader: RentalReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._rental_reader = rental_reader

    async def execute(self, request: ListBookingRequestsRequest) -> ListRentalsQm:
        logger.info("List booking requests: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="rental.read",
            ),
        )

        result = await self._rental_reader.list_rentals(
            organization_id=request.organization_id,
            status="pending",
        )

        logger.info("List booking requests: done.")
        return result
