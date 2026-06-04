import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.transaction_reader import ListTransactionsQm, TransactionReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ListPendingPaymentsRequest:
    organization_id: UUID


class ListPendingPayments:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        transaction_reader: TransactionReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._transaction_reader = transaction_reader

    async def execute(self, request: ListPendingPaymentsRequest) -> ListTransactionsQm:
        logger.info("List pending payments: started.")

        current_user = await self._current_user_service.get_current_user()
        authorize(
            HasPermission(),
            context=PermissionCheckContext(
                subject=current_user,
                required_permission="payment.read",
            ),
        )

        result = await self._transaction_reader.list_transactions(
            organization_id=request.organization_id,
            status="pending",
        )

        logger.info("List pending payments: done.")
        return result
