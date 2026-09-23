"""Trade journal: every trade logged with entry/exit, rationale, expected vs actual P&L."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TradeJournalEntry:
    trade_id: str
    strategy: str
    pair: str
    direction: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime | None = None
    exit_price: float | None = None
    expected_pnl: float = 0.0
    actual_pnl: float = 0.0
    slippage_bps: float = 0.0
    rationale: str = ""
    signal_source: str = ""
    chart_path: str = ""
    metadata: dict = field(default_factory=dict)


_journal: list[TradeJournalEntry] = []


def log_trade(entry: TradeJournalEntry) -> None:
    """Log a trade to the journal."""
    _journal.append(entry)
    logger.info(
        "TRADE %s: %s %s %s entry=%.5f exit=%s pnl=%.2f",
        entry.trade_id, entry.strategy, entry.pair, entry.direction,
        entry.entry_price, entry.exit_price, entry.actual_pnl,
    )

    # Persist to DB
    try:
        from db import SessionLocal
        from db.models import AuditLog
        db = SessionLocal()
        db.add(AuditLog(
            actor=f"trade_journal:{entry.strategy}",
            action="trade_logged",
            details={
                "trade_id": entry.trade_id,
                "pair": entry.pair,
                "direction": entry.direction,
                "entry_price": entry.entry_price,
                "exit_price": entry.exit_price,
                "expected_pnl": entry.expected_pnl,
                "actual_pnl": entry.actual_pnl,
                "slippage_bps": entry.slippage_bps,
                "signal_source": entry.signal_source,
            },
        ))
        db.commit()
        db.close()
    except Exception as e:
        logger.error("Failed to persist trade journal entry: %s", e)


def get_recent_trades(n: int = 50) -> list[TradeJournalEntry]:
    return _journal[-n:]


def get_strategy_trades(strategy: str) -> list[TradeJournalEntry]:
    return [t for t in _journal if t.strategy == strategy]
