import logging
from dataclasses import dataclass

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.client_reader import ClientReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class VerificationStatusQm:
    verification_status: str
    rejection_reason: str | None


class GetMyVerification:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_reader: ClientReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_reader

    async def execute(self) -> VerificationStatusQm | None:
        logger.info("Get my verification: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="mobile.profile",
            ),
        )

        client = await self._client_reader.get_by_user_id(user_id=current_user.id_)
        if client is None:
            logger.info("Get my verification: no client found.")
            return None

        logger.info("Get my verification: done.")
        return VerificationStatusQm(
            verification_status=client.verification_status,
            rejection_reason=client.rejection_reason,
        )
