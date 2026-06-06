import logging
from datetime import timedelta
from uuid import UUID

from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.entities.types_ import NotificationType
from app.core.common.services.notification_service import NotificationService
from app.core.queries.ports.rental_reader import RentalReader

logger = logging.getLogger(__name__)


class CheckOverdueRentals:
    def __init__(
        self,
        utc_timer: UtcTimer,
        rental_reader: RentalReader,
        notification_service: NotificationService,
    ) -> None:
        self._utc_timer = utc_timer
        self._rental_reader = rental_reader
        self._notification_service = notification_service

    async def execute(self, organization_id: UUID) -> int:
        now = self._utc_timer.now.value
        overdue_before = now - timedelta(hours=1)

        rentals = await self._rental_reader.list_active_overdue(
            organization_id=organization_id,
            overdue_before=overdue_before,
        )

        sent = 0
        for rental in rentals:
            try:
                await self._notification_service.send_to_client(
                    client_id=rental["client_id"],
                    organization_id=organization_id,
                    type_=NotificationType.OVERDUE_ALERT,
                    title="Rental Overdue",
                    body="Your rental is overdue. Please return the vehicle immediately to avoid additional charges.",
                    deep_link=f"/rentals/{rental['id']}",
                    metadata={"rental_id": str(rental["id"])},
                )
                sent += 1
            except Exception:
                logger.exception("Failed to send overdue alert for rental %s", rental["id"])

        logger.info("Overdue alerts: sent %d notifications.", sent)
        return sent
