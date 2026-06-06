import logging
from datetime import timedelta
from uuid import UUID

from app.core.commands.ports.utc_timer import UtcTimer
from app.core.common.entities.types_ import NotificationType
from app.core.common.services.notification_service import NotificationService
from app.core.queries.ports.rental_reader import RentalReader

logger = logging.getLogger(__name__)


class CheckReturnReminders:
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
        window_end = now + timedelta(hours=2)

        rentals = await self._rental_reader.list_active_ending_between(
            organization_id=organization_id,
            end_from=window_start,
            end_to=window_end,
        )

        sent = 0
        for rental in rentals:
            try:
                await self._notification_service.send_to_client(
                    client_id=rental["client_id"],
                    organization_id=organization_id,
                    type_=NotificationType.RETURN_REMINDER,
                    title="Return Reminder",
                    body=(
                        f"Your rental return is due at {rental['scheduled_end']:%H:%M}."
                        " Please return the vehicle on time."
                    ),
                    deep_link=f"/rentals/{rental['id']}",
                    metadata={"rental_id": str(rental["id"])},
                )
                sent += 1
            except Exception:
                logger.exception("Failed to send return reminder for rental %s", rental["id"])

        logger.info("Return reminders: sent %d notifications.", sent)
        return sent
