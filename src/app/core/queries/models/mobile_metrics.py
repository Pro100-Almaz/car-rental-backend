from typing import TypedDict


class MobileMetricsQm(TypedDict):
    pending_verifications: int
    pending_bookings: int
    pending_payments: int
    pending_extensions: int
