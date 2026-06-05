import logging
from decimal import Decimal
from typing import TypedDict

from app.core.common.authorization.authorize import authorize
from app.core.common.authorization.current_user_service import CurrentUserService
from app.core.common.authorization.rbac import HasPermission, PermissionCheckContext
from app.core.queries.models.fine import FineQm
from app.core.queries.models.mobile_rental import MobileRentalQm
from app.core.queries.ports.client_reader import ClientReader
from app.core.queries.ports.fine_reader import FineReader
from app.core.queries.ports.mobile_rental_reader import MobileRentalReader

logger = logging.getLogger(__name__)


class OutstandingQm(TypedDict):
    rentals_with_debt: list[MobileRentalQm]
    unpaid_fines: list[FineQm]
    total_debt: Decimal
    total_unpaid_fines: Decimal
    grand_total: Decimal


class GetMyOutstanding:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        client_reader: ClientReader,
        mobile_rental_reader: MobileRentalReader,
        fine_reader: FineReader,
    ) -> None:
        self._current_user_service = current_user_service
        self._client_reader = client_reader
        self._mobile_rental_reader = mobile_rental_reader
        self._fine_reader = fine_reader

    async def execute(self) -> OutstandingQm:
        logger.info("Get my outstanding: started.")

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
            return OutstandingQm(
                rentals_with_debt=[],
                unpaid_fines=[],
                total_debt=Decimal(0),
                total_unpaid_fines=Decimal(0),
                grand_total=Decimal(0),
            )

        completed_rentals = await self._mobile_rental_reader.list_by_client(
            client_id=client.id,
            status="completed",
        )
        rentals_with_debt = [
            r
            for r in completed_rentals["rentals"]
            if r.actual_total is not None and r.actual_total > (r.prepayment_amount + r.deposit_refund_amount)
        ]
        total_debt = (
            sum((r.actual_total - r.prepayment_amount) for r in rentals_with_debt) if rentals_with_debt else Decimal(0)
        )

        fines_result = await self._fine_reader.list_fines(
            organization_id=client.organization_id,
            client_id=client.id,
            status="charged_to_client",
        )
        unpaid_fines = fines_result["fines"]
        total_unpaid_fines = sum(f.amount for f in unpaid_fines) if unpaid_fines else Decimal(0)

        logger.info("Get my outstanding: done.")
        return OutstandingQm(
            rentals_with_debt=rentals_with_debt,
            unpaid_fines=unpaid_fines,
            total_debt=total_debt,
            total_unpaid_fines=total_unpaid_fines,
            grand_total=total_debt + total_unpaid_fines,
        )
