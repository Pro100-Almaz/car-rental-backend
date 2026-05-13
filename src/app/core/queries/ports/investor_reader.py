from abc import abstractmethod
from typing import Protocol, TypedDict
from uuid import UUID

from app.core.queries.models.investor import InvestorQm
from app.core.queries.models.investor_payout import InvestorPayoutQm
from app.core.queries.models.vehicle_investor import VehicleInvestorQm


class ListInvestorsQm(TypedDict):
    investors: list[InvestorQm]
    total: int


class ListVehicleInvestorsQm(TypedDict):
    vehicle_investors: list[VehicleInvestorQm]
    total: int


class ListInvestorPayoutsQm(TypedDict):
    payouts: list[InvestorPayoutQm]
    total: int


class InvestorReader(Protocol):
    @abstractmethod
    async def get_by_id(
        self,
        *,
        investor_id: UUID,
    ) -> InvestorQm | None: ...

    @abstractmethod
    async def list_investors(
        self,
        *,
        organization_id: UUID,
        type_: str | None = None,
    ) -> ListInvestorsQm: ...

    @abstractmethod
    async def list_vehicle_investors(
        self,
        *,
        investor_id: UUID,
    ) -> ListVehicleInvestorsQm: ...

    @abstractmethod
    async def list_investor_payouts(
        self,
        *,
        investor_id: UUID,
        status: str | None = None,
    ) -> ListInvestorPayoutsQm: ...
