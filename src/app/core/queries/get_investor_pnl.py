import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.core.queries.models.investor_pnl import InvestorPnlQm, InvestorVehiclePnlQm
from app.core.queries.ports.investor_reader import InvestorReader
from app.core.queries.ports.vehicle_financials_reader import VehicleFinancialsReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetInvestorPnlRequest:
    investor_id: UUID
    date_from: date
    date_to: date


class GetInvestorPnl:
    def __init__(
        self,
        investor_reader: InvestorReader,
        vehicle_financials_reader: VehicleFinancialsReader,
    ) -> None:
        self._investor_reader = investor_reader
        self._vehicle_financials_reader = vehicle_financials_reader

    async def execute(self, request: GetInvestorPnlRequest) -> InvestorPnlQm:
        logger.info("Get investor PnL: started.")

        links = await self._investor_reader.list_vehicle_investors(
            investor_id=request.investor_id,
        )

        vehicles: list[InvestorVehiclePnlQm] = []
        total_revenue = Decimal(0)
        total_expenses = Decimal(0)
        total_net_profit = Decimal(0)
        total_investor_share = Decimal(0)

        for link in links["vehicle_investors"]:
            financials = await self._vehicle_financials_reader.get_financials(
                vehicle_id=link.vehicle_id,
                date_from=request.date_from,
                date_to=request.date_to,
            )

            share_pct = link.share_percentage / Decimal(100)
            investor_share = (financials.net_profit * share_pct).quantize(Decimal("0.01"))

            vehicles.append(
                InvestorVehiclePnlQm(
                    vehicle_id=link.vehicle_id,
                    share_percentage=link.share_percentage,
                    total_revenue=financials.total_revenue,
                    total_expenses=financials.total_expenses,
                    net_profit=financials.net_profit,
                    investor_share=investor_share,
                    utilization_percent=financials.utilization_percent,
                )
            )

            total_revenue += financials.total_revenue
            total_expenses += financials.total_expenses
            total_net_profit += financials.net_profit
            total_investor_share += investor_share

        logger.info("Get investor PnL: done.")
        return InvestorPnlQm(
            investor_id=request.investor_id,
            period_from=request.date_from.isoformat(),
            period_to=request.date_to.isoformat(),
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            total_net_profit=total_net_profit,
            total_investor_share=total_investor_share,
            vehicles=vehicles,
        )
