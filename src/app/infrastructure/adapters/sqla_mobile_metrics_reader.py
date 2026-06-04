from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries.models.mobile_metrics import MobileMetricsQm
from app.core.queries.ports.mobile_metrics_reader import MobileMetricsReader
from app.infrastructure.exceptions import ReaderError
from app.infrastructure.persistence_sqla.mappings.client import clients_table
from app.infrastructure.persistence_sqla.mappings.extension_request import extension_requests_table
from app.infrastructure.persistence_sqla.mappings.rental import rentals_table
from app.infrastructure.persistence_sqla.mappings.transaction import transactions_table


class SqlaMobileMetricsReader(MobileMetricsReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_metrics(
        self,
        *,
        organization_id: UUID,
    ) -> MobileMetricsQm:
        try:
            verifications = await self._session.execute(
                select(func.count())
                .select_from(clients_table)
                .where(clients_table.c.organization_id == organization_id)
                .where(clients_table.c.verification_status == "pending")
            )
            bookings = await self._session.execute(
                select(func.count())
                .select_from(rentals_table)
                .where(rentals_table.c.organization_id == organization_id)
                .where(rentals_table.c.status == "pending")
                .where(rentals_table.c.source == "mobile")
            )
            payments = await self._session.execute(
                select(func.count())
                .select_from(transactions_table)
                .where(transactions_table.c.organization_id == organization_id)
                .where(transactions_table.c.status == "pending")
                .where(transactions_table.c.source == "mobile")
            )
            extensions = await self._session.execute(
                select(func.count())
                .select_from(extension_requests_table)
                .where(extension_requests_table.c.organization_id == organization_id)
                .where(extension_requests_table.c.status == "pending")
            )

            return MobileMetricsQm(
                pending_verifications=verifications.scalar_one(),
                pending_bookings=bookings.scalar_one(),
                pending_payments=payments.scalar_one(),
                pending_extensions=extensions.scalar_one(),
            )
        except SQLAlchemyError as e:
            raise ReaderError from e
