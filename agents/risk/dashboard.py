"""Live risk state dashboard and auto-pause logic."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from agents.risk.limits import RiskLimits, check_all

logger = logging.getLogger(__name__)


@dataclass
class RiskState:
    current_drawdown: float
    daily_pnl_pct: float
    current_leverage: float
    largest_position_pct: float
    total_exposure: float
    violations: list[str]
    should_pause: bool


def compute_risk_state(
    equity: float,
    peak_equity: float,
    daily_start_equity: float,
    total_position_value: float,
    largest_position_value: float,
) -> RiskState:
    """Aggregate live risk metrics and check for limit breaches."""
    drawdown = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0.0
    daily_pnl = (equity - daily_start_equity) / daily_start_equity if daily_start_equity > 0 else 0.0
    leverage = total_position_value / equity if equity > 0 else 0.0
    concentration = largest_position_value / equity if equity > 0 else 0.0

    violations = check_all(
        current_drawdown=drawdown,
        daily_pnl_pct=daily_pnl,
        current_leverage=leverage,
        position_pct=concentration,
    )

    should_pause = len(violations) > 0

    if should_pause:
        logger.warning("RISK LIMIT BREACHED — auto-pause triggered: %s", violations)

    return RiskState(
        current_drawdown=round(drawdown, 6),
        daily_pnl_pct=round(daily_pnl, 6),
        current_leverage=round(leverage, 4),
        largest_position_pct=round(concentration, 4),
        total_exposure=round(total_position_value, 2),
        violations=violations,
        should_pause=should_pause,
    )


def auto_pause_strategy(strategy_id: int, reason: str) -> None:
    """Pause a strategy in the DB when a risk limit is breached."""
    from db import SessionLocal
    from db.models import Strategy, StrategyStatus

    db = SessionLocal()
    try:
        strat = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if strat and strat.status != StrategyStatus.PAUSED:
            strat.status = StrategyStatus.PAUSED
            db.commit()
            logger.warning("Strategy %s PAUSED: %s", strat.name, reason)
    finally:
        db.close()
