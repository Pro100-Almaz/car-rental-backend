import logging
from dataclasses import dataclass

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.ports.client_reader import ClientReader
from app.core.queries.ports.transaction_reader import ListTransactionsQm, TransactionReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetMyPaymentsRequest:
    status: str | None = None
    type_: str | None = None


class GetMyPayments:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_reader: ClientReader,
        transaction_reader: TransactionReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_reader
        self._transaction_reader = transaction_reader

    async def execute(self, request: GetMyPaymentsRequest) -> ListTransactionsQm:
        logger.info("Get my payments: started.")

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
            return ListTransactionsQm(transactions=[], total=0)

        result = await self._transaction_reader.list_transactions(
            organization_id=client.organization_id,
            client_id=client.id,
            status=request.status,
            type_=request.type_,
        )

        logger.info("Get my payments: done.")
        return result
