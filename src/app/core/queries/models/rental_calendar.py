from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CalendarSlotQm:
    rental_id: UUID
    client_id: UUID
    client_name: str
    status: str
    scheduled_start: datetime
    scheduled_end: datetime


@dataclass(frozen=True, slots=True)
class CalendarVehicleQm:
    vehicle_id: UUID
    nickname: str | None
    license_plate: str
    make: str
    model: str
    category: str
    slots: list[CalendarSlotQm]


class RentalCalendarQm(TypedDict):
    vehicles: list[CalendarVehicleQm]
    month: str
