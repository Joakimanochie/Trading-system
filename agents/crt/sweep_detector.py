"""CRT Step 2: Detect liquidity sweeps on the anchor candle range."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from agents.crt.anchor import AnchorCandle


class SweepType(str, Enum):
    SWEEP_LOW = "SWEEP_LOW"
    SWEEP_HIGH = "SWEEP_HIGH"
    INVALIDATED = "INVALIDATED"
    NONE = "NONE"


@dataclass
class SweepResult:
    sweep_type: SweepType
    sweep_candle_idx: int | None = None
    direction: str | None = None  # LONG or SHORT


def detect_sweep(htf_data: pd.DataFrame, anchor: AnchorCandle, max_candles: int = 3) -> SweepResult:
    """Scan candles after the anchor for a sweep.

    Bullish: candle's low < CRT_LOW AND closes back above CRT_LOW.
    Bearish: candle's high > CRT_HIGH AND closes back below CRT_HIGH.
    3-Candle Rule: invalidate if no confirmation within max_candles.
    """
    anchor_idx = htf_data.index.get_loc(anchor.timestamp)
    scan_start = anchor_idx + 1
    scan_end = min(scan_start + max_candles, len(htf_data))

    for i in range(scan_start, scan_end):
        candle = htf_data.iloc[i]
        h, l, c = float(candle["high"]), float(candle["low"]), float(candle["close"])

        if l < anchor.crt_low and c > anchor.crt_low:
            return SweepResult(SweepType.SWEEP_LOW, i, "LONG")
        if h > anchor.crt_high and c < anchor.crt_high:
            return SweepResult(SweepType.SWEEP_HIGH, i, "SHORT")
        if c > anchor.crt_high or c < anchor.crt_low:
            return SweepResult(SweepType.INVALIDATED, i)

    return SweepResult(SweepType.NONE)
