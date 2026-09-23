"""Hard risk limits enforcement."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from config import settings

logger = logging.getLogger(__name__)


class RiskLimitBreached(Exception):
    """Raised when a hard risk limit is violated."""
    pass


@dataclass
class RiskLimits:
    max_drawdown_pct: float
    daily_loss_limit_pct: float
    max_leverage: float
    max_position_concentration: float

    @classmethod
    def from_settings(cls) -> "RiskLimits":
        return cls(
            max_drawdown_pct=settings.risk_max_drawdown_pct,
            daily_loss_limit_pct=settings.risk_daily_loss_limit_pct,
            max_leverage=settings.risk_max_leverage,
            max_position_concentration=settings.risk_max_position_concentration,
        )


def check_drawdown(current_drawdown: float, limits: RiskLimits | None = None) -> None:
    if limits is None:
        limits = RiskLimits.from_settings()
    if current_drawdown >= limits.max_drawdown_pct:
        raise RiskLimitBreached(
            f"Drawdown {current_drawdown:.2%} exceeds limit {limits.max_drawdown_pct:.2%}"
        )


def check_daily_loss(daily_pnl_pct: float, limits: RiskLimits | None = None) -> None:
    if limits is None:
        limits = RiskLimits.from_settings()
    if daily_pnl_pct <= -limits.daily_loss_limit_pct:
        raise RiskLimitBreached(
            f"Daily loss {daily_pnl_pct:.2%} exceeds limit {limits.daily_loss_limit_pct:.2%}"
        )


def check_leverage(current_leverage: float, limits: RiskLimits | None = None) -> None:
    if limits is None:
        limits = RiskLimits.from_settings()
    if current_leverage > limits.max_leverage:
        raise RiskLimitBreached(
            f"Leverage {current_leverage:.2f}x exceeds limit {limits.max_leverage:.2f}x"
        )


def check_concentration(position_pct: float, limits: RiskLimits | None = None) -> None:
    if limits is None:
        limits = RiskLimits.from_settings()
    if position_pct > limits.max_position_concentration:
        raise RiskLimitBreached(
            f"Position concentration {position_pct:.2%} exceeds limit {limits.max_position_concentration:.2%}"
        )


def check_all(
    current_drawdown: float = 0.0,
    daily_pnl_pct: float = 0.0,
    current_leverage: float = 0.0,
    position_pct: float = 0.0,
    limits: RiskLimits | None = None,
) -> list[str]:
    """Run all limit checks. Returns list of violations (empty = all clear)."""
    if limits is None:
        limits = RiskLimits.from_settings()
    violations = []
    for check, val in [
        (check_drawdown, current_drawdown),
        (check_daily_loss, daily_pnl_pct),
        (check_leverage, current_leverage),
        (check_concentration, position_pct),
    ]:
        try:
            check(val, limits)
        except RiskLimitBreached as e:
            violations.append(str(e))
    return violations
