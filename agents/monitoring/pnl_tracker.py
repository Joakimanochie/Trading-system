"""Live P&L tracking per strategy and portfolio total."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PnLSnapshot:
    timestamp: datetime
    strategy_name: str
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    equity: float


@dataclass
class PortfolioPnL:
    timestamp: datetime
    total_equity: float
    total_unrealized: float
    total_realized: float
    daily_pnl: float
    per_strategy: list[PnLSnapshot]


def compute_strategy_pnl(
    strategy_name: str,
    positions: list[dict],
    closed_trades: list[dict],
    initial_capital: float,
) -> PnLSnapshot:
    """Compute P&L for a single strategy."""
    unrealized = sum(p.get("unrealized_pnl", 0) for p in positions)
    realized = sum(t.get("pnl", 0) for t in closed_trades)
    total = unrealized + realized
    equity = initial_capital + total

    return PnLSnapshot(
        timestamp=datetime.utcnow(),
        strategy_name=strategy_name,
        unrealized_pnl=round(unrealized, 2),
        realized_pnl=round(realized, 2),
        total_pnl=round(total, 2),
        equity=round(equity, 2),
    )


def compute_portfolio_pnl(
    strategy_snapshots: list[PnLSnapshot],
    daily_start_equity: float,
) -> PortfolioPnL:
    """Aggregate P&L across all strategies."""
    total_equity = sum(s.equity for s in strategy_snapshots)
    total_unrealized = sum(s.unrealized_pnl for s in strategy_snapshots)
    total_realized = sum(s.realized_pnl for s in strategy_snapshots)
    daily_pnl = total_equity - daily_start_equity

    return PortfolioPnL(
        timestamp=datetime.utcnow(),
        total_equity=round(total_equity, 2),
        total_unrealized=round(total_unrealized, 2),
        total_realized=round(total_realized, 2),
        daily_pnl=round(daily_pnl, 2),
        per_strategy=strategy_snapshots,
    )


def store_snapshot(snapshot: PortfolioPnL) -> None:
    """Persist a P&L snapshot to the database."""
    try:
        from db import SessionLocal
        from db.models import PerformanceRecord
        db = SessionLocal()
        # Store as a lightweight record
        record = PerformanceRecord(
            strategy_id=1,  # portfolio-level
            period_start=snapshot.timestamp,
            period_end=snapshot.timestamp,
            sharpe_ratio=None,
            equity_curve=[snapshot.total_equity],
            record_type="pnl_snapshot",
            metadata_json={
                "total_equity": snapshot.total_equity,
                "daily_pnl": snapshot.daily_pnl,
                "unrealized": snapshot.total_unrealized,
                "realized": snapshot.total_realized,
            },
        )
        db.add(record)
        db.commit()
        db.close()
    except Exception as e:
        logger.error("Failed to store PnL snapshot: %s", e)
