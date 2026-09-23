"""Fair Value Gap (FVG) detection with ATR-based minimum size — shared by CRT and Photon."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class FVG:
    direction: str  # "bullish" or "bearish"
    high: float
    low: float
    gap_size: float
    candle_index: int
    timestamp: datetime


def detect_fvgs(
    data: pd.DataFrame,
    atr_value: float = 0.0,
    min_atr_mult: float = 0.25,
    high_col: str = "high",
    low_col: str = "low",
) -> list[FVG]:
    """Detect 3-candle FVGs (imbalances).

    Bullish FVG: candle1.high < candle3.low (gap up).
    Bearish FVG: candle3.high < candle1.low (gap down).
    Gap must be >= min_atr_mult * atr_value to qualify.
    """
    fvgs: list[FVG] = []
    min_size = atr_value * min_atr_mult

    for i in range(2, len(data)):
        c1_high = float(data.iloc[i - 2][high_col])
        c3_low = float(data.iloc[i][low_col])
        c1_low = float(data.iloc[i - 2][low_col])
        c3_high = float(data.iloc[i][high_col])

        # Bullish FVG
        if c1_high < c3_low:
            gap = c3_low - c1_high
            if gap >= min_size:
                fvgs.append(FVG(
                    direction="bullish",
                    high=c3_low,
                    low=c1_high,
                    gap_size=gap,
                    candle_index=i,
                    timestamp=data.index[i],
                ))

        # Bearish FVG
        if c3_high < c1_low:
            gap = c1_low - c3_high
            if gap >= min_size:
                fvgs.append(FVG(
                    direction="bearish",
                    high=c1_low,
                    low=c3_high,
                    gap_size=gap,
                    candle_index=i,
                    timestamp=data.index[i],
                ))

    return fvgs
