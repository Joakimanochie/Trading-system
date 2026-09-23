"""Signal router: all signals (CRT + Photon + other) → Risk Agent → execution mode → audit log."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from agents.risk.limits import check_all, RiskLimitBreached
from agents.risk.sizer import size_position
from agents.execution.modes import get_current_mode, ExecutionMode, is_signal_expired
from orchestrator.audit_log import write_audit_log

logger = logging.getLogger(__name__)


@dataclass
class RoutedSignal:
    signal_id: str
    source_agent: str
    pair: str
    direction: str
    entry_price: float
    sl: float
    tp1: float
    position_size: float | None = None
    risk_violations: list[str] | None = None
    routed_to: str = ""  # "approval_queue" or "auto_execute" or "rejected"
    timestamp: datetime | None = None


def route_signal(
    signal_id: str,
    source_agent: str,
    pair: str,
    direction: str,
    entry_price: float,
    sl: float,
    tp1: float,
    capital: float = 100_000,
    win_rate: float = 0.5,
    profit_factor: float = 1.5,
    current_drawdown: float = 0.0,
    daily_pnl_pct: float = 0.0,
    current_leverage: float = 0.0,
    position_pct: float = 0.0,
) -> RoutedSignal:
    """Route a signal through the risk check → execution mode pipeline."""
    routed = RoutedSignal(
        signal_id=signal_id,
        source_agent=source_agent,
        pair=pair,
        direction=direction,
        entry_price=entry_price,
        sl=sl,
        tp1=tp1,
        timestamp=datetime.utcnow(),
    )

    # Step 1: Risk limit check
    violations = check_all(
        current_drawdown=current_drawdown,
        daily_pnl_pct=daily_pnl_pct,
        current_leverage=current_leverage,
        position_pct=position_pct,
    )

    if violations:
        routed.risk_violations = violations
        routed.routed_to = "rejected"
        logger.warning("Signal %s REJECTED by risk: %s", signal_id, violations)
        write_audit_log(
            actor="signal_router",
            action="signal_rejected",
            details={"signal_id": signal_id, "source": source_agent, "violations": violations},
            outcome="rejected",
        )
        return routed

    # Step 2: Position sizing
    pos = size_position(capital, win_rate, profit_factor, entry_price, sl)
    routed.position_size = pos.position_dollars

    # Step 3: Execution mode routing
    mode = get_current_mode()
    if mode == ExecutionMode.AUTO:
        routed.routed_to = "auto_execute"
    else:
        routed.routed_to = "approval_queue"

    logger.info(
        "Signal %s from %s → %s (size=$%.2f)",
        signal_id, source_agent, routed.routed_to, pos.position_dollars,
    )

    write_audit_log(
        actor="signal_router",
        action="signal_routed",
        details={
            "signal_id": signal_id,
            "source": source_agent,
            "pair": pair,
            "direction": direction,
            "position_size": pos.position_dollars,
            "mode": mode.value,
            "routed_to": routed.routed_to,
        },
        outcome="routed",
    )

    return routed
