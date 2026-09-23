"""Reconstruct the forming HTF candle from closed LTF bars.

This enables intra-candle sweep detection — the agent doesn't wait for
the H4 close to detect a sweep, it watches LTF bars in real time.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd


# H4 candle duration in various LTF bar counts
HTF_DURATION = {
    "H4": timedelta(hours=4),
    "H1": timedelta(hours=1),
    "D1": timedelta(days=1),
}


@dataclass
class FormingCandle:
    htf_open_time: datetime
    open: float
    high: float
    low: float
    close: float
    bar_count: int
    is_complete: bool = False


def get_htf_open_time(timestamp: datetime, htf: str = "H4") -> datetime:
    """Round down a timestamp to the start of its HTF candle."""
    if htf == "H4":
        hour = (timestamp.hour // 4) * 4
        return timestamp.replace(hour=hour, minute=0, second=0, microsecond=0)
    elif htf == "H1":
        return timestamp.replace(minute=0, second=0, microsecond=0)
    elif htf == "D1":
        return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    return timestamp


def reconstruct_forming_candle(
    ltf_data: pd.DataFrame,
    htf: str = "H4",
) -> FormingCandle | None:
    """Build the current forming HTF candle from closed LTF bars.

    Returns the live high/low/close of the candle that hasn't closed yet.
    """
    if len(ltf_data) == 0:
        return None

    last_time = ltf_data.index[-1]
    htf_open = get_htf_open_time(last_time, htf)
    duration = HTF_DURATION.get(htf, timedelta(hours=4))

    bars_in_candle = ltf_data[ltf_data.index >= htf_open]
    if len(bars_in_candle) == 0:
        return None

    o = float(bars_in_candle.iloc[0]["open"])
    h = float(bars_in_candle["high"].max())
    l = float(bars_in_candle["low"].min())
    c = float(bars_in_candle.iloc[-1]["close"])

    is_complete = (last_time - htf_open) >= duration

    return FormingCandle(
        htf_open_time=htf_open,
        open=o,
        high=h,
        low=l,
        close=c,
        bar_count=len(bars_in_candle),
        is_complete=is_complete,
    )
