from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ActiveRentalItemQm:
    rental_id: UUID
    vehicle_id: UUID
    vehicle_nickname: str | None
    license_plate: str
    client_id: UUID
    client_name: str
    scheduled_end: datetime
    hours_remaining: int


@dataclass(frozen=True, slots=True)
class ReturnTodayItemQm:
    rental_id: UUID
    vehicle_id: UUID
    vehicle_nickname: str | None
    license_plate: str
    client_name: str
    scheduled_end: datetime


@dataclass(frozen=True, slots=True)
class DashboardActiveRentalsQm:
    active_rentals: list[ActiveRentalItemQm]
    returns_today_count: int
    returns_today: list[ReturnTodayItemQm]
