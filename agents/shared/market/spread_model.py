"""Session-aware spread model for CRT backtesting and live risk checks.

CRT trades session opens when spreads widen 2-5x. A flat cost model
understates real costs. This module applies per-pair, time-of-day spreads.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, time

logger = logging.getLogger(__name__)

# Base spreads in pips (mid-session, normal conditions)
BASE_SPREADS_PIPS = {
    "EURUSD": 0.8,
    "GBPUSD": 1.0,
    "USDCHF": 1.2,
    "USDCAD": 1.2,
    "AUDUSD": 1.0,
    "USDJPY": 0.9,
    "NZDUSD": 1.5,
    "XAUUSD": 25.0,   # in cents, not pips
    "BTCUSD": 50.0,   # in dollars
    "ETHUSD": 3.0,    # in dollars
}

# Pip values (how to convert pips to price units)
PIP_VALUES = {
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCHF": 0.0001,
    "USDCAD": 0.0001, "AUDUSD": 0.0001, "NZDUSD": 0.0001,
    "USDJPY": 0.01,
    "XAUUSD": 0.01,   # cents
    "BTCUSD": 1.0,    # dollars
    "ETHUSD": 1.0,
}

SESSION_OPEN_WINDOWS = [
    (time(7, 0), time(7, 15)),   # London open (UTC)
    (time(12, 0), time(12, 15)), # NY open (UTC)
]

DEFAULT_OPEN_MULT = 2.5
DEFAULT_OPEN_WINDOW_MINS = 15


@dataclass
class SpreadEstimate:
    pair: str
    base_spread_price: float
    effective_spread_price: float
    multiplier: float
    in_open_window: bool


def is_in_session_open(utc_time: datetime, window_mins: int = DEFAULT_OPEN_WINDOW_MINS) -> bool:
    """Check if the current UTC time falls within a session-open spread window."""
    t = utc_time.time()
    for start, _ in SESSION_OPEN_WINDOWS:
        end_hour = start.hour
        end_min = start.minute + window_mins
        if end_min >= 60:
            end_hour += 1
            end_min -= 60
        end = time(end_hour % 24, end_min)
        if start <= t <= end:
            return True
    return False


def get_spread(
    pair: str,
    utc_time: datetime | None = None,
    open_mult: float = DEFAULT_OPEN_MULT,
) -> SpreadEstimate:
    """Get the estimated spread for a pair at a given time."""
    base_pips = BASE_SPREADS_PIPS.get(pair, 2.0)
    pip_value = PIP_VALUES.get(pair, 0.0001)
    base_price = base_pips * pip_value

    in_open = False
    mult = 1.0
    if utc_time is not None:
        in_open = is_in_session_open(utc_time)
        if in_open:
            mult = open_mult

    return SpreadEstimate(
        pair=pair,
        base_spread_price=base_price,
        effective_spread_price=base_price * mult,
        multiplier=mult,
        in_open_window=in_open,
    )


def spread_cost_bps(pair: str, entry_price: float, utc_time: datetime | None = None) -> float:
    """Get the one-way spread cost in basis points."""
    estimate = get_spread(pair, utc_time)
    if entry_price == 0:
        return 0.0
    return (estimate.effective_spread_price / entry_price) * 10_000
