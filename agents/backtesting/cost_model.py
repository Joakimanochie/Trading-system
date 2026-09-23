"""Transaction cost model: commission + spread + slippage."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostModel:
    commission_bps: float = 5.0
    spread_bps: float = 2.0
    slippage_bps: float = 2.0

    @property
    def total_bps(self) -> float:
        return self.commission_bps + self.spread_bps + self.slippage_bps

    @property
    def total_pct(self) -> float:
        return self.total_bps / 10_000

    def round_trip_cost(self, notional: float) -> float:
        return notional * self.total_pct * 2

    def apply_to_returns(self, gross_returns, n_trades: int, n_periods: int) -> float:
        """Subtract per-trade costs from total gross return.

        Returns net total return as a fraction (e.g. 0.12 = 12%).
        """
        cost_per_trade = self.total_pct * 2  # round-trip
        total_cost = cost_per_trade * n_trades
        return gross_returns - total_cost
