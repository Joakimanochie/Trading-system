"""Kelly criterion position sizing."""
from __future__ import annotations

from config import settings


def kelly_fraction(win_rate: float, profit_factor: float) -> float:
    """Compute the optimal Kelly fraction: f* = W - (1-W)/R.

    W = win rate (0-1), R = profit factor (avg_win / avg_loss).
    Returns the fraction of capital to risk per trade.
    """
    if profit_factor <= 0:
        return 0.0
    f = win_rate - (1 - win_rate) / profit_factor
    return max(f, 0.0)


def fractional_kelly(win_rate: float, profit_factor: float, fraction: float | None = None) -> float:
    """Apply fractional Kelly (default from settings.risk_kelly_fraction)."""
    if fraction is None:
        fraction = settings.risk_kelly_fraction
    return kelly_fraction(win_rate, profit_factor) * fraction
