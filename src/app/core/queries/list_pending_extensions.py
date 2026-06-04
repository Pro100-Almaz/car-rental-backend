import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.models.extension_request import ListExtensionRequestsQm
from app.core.queries.ports.extension_request_reader import ExtensionRequestReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListPendingExtensionsRequest:
    organization_id: UUID


class ListPendingExtensions:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        extension_request_reader: ExtensionRequestReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._extension_request_reader = extension_request_reader

    async def execute(self, request: ListPendingExtensionsRequest) -> ListExtensionRequestsQm:
        logger.info("List pending extensions: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="rental.read",
            ),
        )

        return await self._extension_request_reader.list_pending(
            organization_id=request.organization_id,
        )
