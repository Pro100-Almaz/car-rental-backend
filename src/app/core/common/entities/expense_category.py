from app.core.common.entities.base import Entity
from app.core.common.entities.types_ import ExpenseCategoryId, ExpenseCategoryType, OrganizationId
from app.core.common.value_objects.utc_datetime import UtcDatetime


class ExpenseCategory(Entity[ExpenseCategoryId]):
    def __init__(
        self,
        *,
        id_: ExpenseCategoryId,
        organization_id: OrganizationId,
        name: str,
        type_: ExpenseCategoryType,
        is_system: bool,
        sort_order: int,
        is_active: bool,
        created_at: UtcDatetime,
    ) -> None:
        super().__init__(id_=id_)
        self.organization_id = organization_id
        self.name = name
        self.type_ = type_
        self.is_system = is_system
        self.sort_order = sort_order
        self.is_active = is_active
        self._created_at = created_at

    @property
    def created_at(self) -> UtcDatetime:
        return self._created_at
