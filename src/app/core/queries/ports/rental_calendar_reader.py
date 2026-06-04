from abc import abstractmethod
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.core.queries.models.rental_calendar import RentalCalendarQm


class RentalCalendarReader(Protocol):
    @abstractmethod
    async def get_calendar(
        self,
        *,
        organization_id: UUID,
        month_start: datetime,
        month_end: datetime,
    ) -> RentalCalendarQm: ...
