from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import (
    OrganizationId,
    RentalId,
    ServiceTaskId,
    ServiceTaskType,
    TaskPriority,
    TaskStatus,
    UserId,
    VehicleId,
)
from app.core.common.value_objects.utc_datetime import UtcDatetime


class ServiceTask(Entity[ServiceTaskId]):
    def __init__(
        self,
        *,
        id_: ServiceTaskId,
        organization_id: OrganizationId,
        vehicle_id: VehicleId,
        rental_id: RentalId | None,
        assigned_to: UserId | None,
        task_type: ServiceTaskType,
        priority: TaskPriority,
        status: TaskStatus,
        description: str | None,
        estimated_cost: Decimal | None,
        actual_cost: Decimal | None,
        proof_photos: list[Any] | None,
        notes: str | None,
        due_at: datetime | None,
        completed_at: datetime | None,
        created_at: UtcDatetime,
        updated_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.vehicle_id = vehicle_id
        self.rental_id = rental_id
        self.assigned_to = assigned_to
        self.task_type = task_type
        self.priority = priority
        self.status = status
        self.description = description
        self.estimated_cost = estimated_cost
        self.actual_cost = actual_cost
        self.proof_photos = proof_photos
        self.notes = notes
        self.due_at = due_at
        self.completed_at = completed_at
        self._created_at = created_at
        self.updated_at = updated_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
