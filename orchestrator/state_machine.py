"""Strategy lifecycle state machine.

States: IDEA_PROPOSED → BACKTESTING → RISK_REVIEW → PAPER_TRADING → LIVE_TRADING → PAUSED / RETIRED
CRT/Photon agents enter at BACKTESTING (no IDEA_PROPOSED stage).
State persistence: stored in DB via Strategy.status, survives restarts.
"""
from __future__ import annotations

import logging
from datetime import datetime

from db.models import Strategy, StrategyStatus

logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    StrategyStatus.IDEA_PROPOSED: [StrategyStatus.BACKTESTING, StrategyStatus.RETIRED],
    StrategyStatus.BACKTESTING: [StrategyStatus.RISK_REVIEW, StrategyStatus.RETIRED],
    StrategyStatus.RISK_REVIEW: [StrategyStatus.PAPER_TRADING, StrategyStatus.RETIRED],
    StrategyStatus.PAPER_TRADING: [StrategyStatus.LIVE_TRADING, StrategyStatus.PAUSED, StrategyStatus.RETIRED],
    StrategyStatus.LIVE_TRADING: [StrategyStatus.PAUSED, StrategyStatus.RETIRED],
    StrategyStatus.PAUSED: [StrategyStatus.LIVE_TRADING, StrategyStatus.PAPER_TRADING, StrategyStatus.RETIRED],
    StrategyStatus.RETIRED: [],
}


class InvalidTransition(Exception):
    pass


def transition(strategy_id: int, target_status: StrategyStatus, actor: str = "system") -> Strategy:
    """Transition a strategy to a new lifecycle state.

    Validates the transition is allowed, persists to DB, and writes an audit log entry.
    """
    from db import SessionLocal
    from orchestrator.audit_log import write_audit_log

    db = SessionLocal()
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        current = strategy.status
        allowed = VALID_TRANSITIONS.get(current, [])

        if target_status not in allowed:
            raise InvalidTransition(
                f"Cannot transition {strategy.name} from {current.value} to {target_status.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

        old_status = current.value
        strategy.status = target_status
        db.commit()
        db.refresh(strategy)

        logger.info("Strategy %s: %s → %s (by %s)", strategy.name, old_status, target_status.value, actor)

        write_audit_log(
            actor=actor,
            action="strategy_transition",
            strategy_id=str(strategy_id),
            details={"from": old_status, "to": target_status.value},
            outcome="success",
        )

        return strategy
    finally:
        db.close()


def get_strategy_state(strategy_id: int) -> StrategyStatus | None:
    """Read current state from DB."""
    from db import SessionLocal
    db = SessionLocal()
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        return strategy.status if strategy else None
    finally:
        db.close()
