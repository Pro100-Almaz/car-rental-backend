import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.queries.models.rental_calendar import RentalCalendarQm
from app.core.queries.ports.rental_calendar_reader import RentalCalendarReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetRentalCalendarRequest:
    organization_id: UUID
    month_start: datetime
    month_end: datetime


class GetRentalCalendar:
    def __init__(
        self,
        rental_calendar_reader: RentalCalendarReader,
    ) -> None:
        self._reader = rental_calendar_reader

    async def execute(self, request: GetRentalCalendarRequest) -> RentalCalendarQm:
        logger.info("Get rental calendar: started.")

        result = await self._reader.get_calendar(
            organization_id=request.organization_id,
            month_start=request.month_start,
            month_end=request.month_end,
        )

        logger.info("Get rental calendar: done.")
        return result
