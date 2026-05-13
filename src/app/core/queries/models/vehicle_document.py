from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import TypedDict
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class VehicleDocumentQm:
    id: UUID
    vehicle_id: UUID
    document_type: str
    name: str
    url: str
    expiry_date: date | None
    created_at: datetime


class ListVehicleDocumentsQm(TypedDict):
    documents: list[VehicleDocumentQm]
    total: int
