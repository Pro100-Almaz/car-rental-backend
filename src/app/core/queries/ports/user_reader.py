from abc import abstractmethod
from typing import Protocol, TypedDict

from app.core.common.entities.user import User
from app.core.queries.models.user import UserQm
from app.core.queries.query_support.offset_pagination import OffsetPaginationParams
from app.core.queries.query_support.sorting import SortingParams


class ListUsersQm(TypedDict):
    users: list[UserQm]
    total: int
    limit: int
    offset: int


class UserReader(Protocol):
    @abstractmethod
    async def list_users(
        self,
        *,
        pagination: OffsetPaginationParams,
        sorting: SortingParams,
    ) -> ListUsersQm: ...

    @abstractmethod
    def row_to_qm(self, row: User) -> UserQm | None: ...
