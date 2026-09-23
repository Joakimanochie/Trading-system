"""CRT Step 1: Identify the anchor candle (most recently closed HTF candle)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class AnchorCandle:
    timestamp: datetime
    pair: str
    htf: str
    open: float
    high: float
    low: float
    close: float
    crt_high: float
    crt_low: float
    crt_eq: float


def identify_anchor(htf_data: pd.DataFrame, pair: str, htf: str) -> AnchorCandle | None:
    """Return the most recently closed HTF candle as an AnchorCandle."""
    if len(htf_data) < 2:
        return None
    candle = htf_data.iloc[-2]  # -1 is current (open), -2 is last closed
    h, l = float(candle["high"]), float(candle["low"])
    return AnchorCandle(
        timestamp=candle.name if isinstance(candle.name, datetime) else htf_data.index[-2],
        pair=pair,
        htf=htf,
        open=float(candle["open"]),
        high=h,
        low=l,
        close=float(candle["close"]),
        crt_high=h,
        crt_low=l,
        crt_eq=l + (h - l) * 0.5,
    )
