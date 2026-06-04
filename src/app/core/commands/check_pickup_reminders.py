import logging
from datetime import timedelta
from uuid import UUID

from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.entities.types_ import NotificationType
from app.core.common.services.notification_service import NotificationService
from app.core.queries.ports.rental_reader import RentalReader

logger = logging.getLogger(__name__)


class CheckPickupReminders:
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
        window_start = now
        window_end = now + timedelta(hours=1)

        rentals = await self._rental_reader.list_confirmed_starting_between(
            organization_id=organization_id,
            start_from=window_start,
            start_to=window_end,
        )

        sent = 0
        for rental in rentals:
            try:
                await self._notification_service.send(
                    user_id=rental["client_id"],
                    organization_id=organization_id,
                    type_=NotificationType.PICKUP_REMINDER,
                    title="Pickup Reminder",
                    body=f"Your rental pickup is scheduled for {rental['scheduled_start']:%H:%M}. Don't forget!",
                    deep_link=f"/rentals/{rental['id']}",
                    metadata={"rental_id": str(rental["id"])},
                )
                sent += 1
            except Exception:
                logger.exception("Failed to send pickup reminder for rental %s", rental["id"])

        logger.info("Pickup reminders: sent %d notifications.", sent)
        return sent
