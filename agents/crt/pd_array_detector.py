"""PD Array detector: HTF Fair Value Gaps and prior Daily/Weekly highs/lows.

v1 scope: FVG detection + prior daily/weekly highs/lows.
Order blocks deferred to v1.1.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class PDArray:
    array_type: str  # "fvg" | "prior_high" | "prior_low"
    high: float
    low: float
    timeframe: str
    created_at: datetime
    mitigated: bool = False


def detect_htf_fvgs(
    data: pd.DataFrame,
    min_gap_pct: float = 0.001,
) -> list[PDArray]:
    """Detect 3-candle Fair Value Gaps on HTF data."""
    fvgs: list[PDArray] = []
    if len(data) < 3:
        return fvgs

    for i in range(2, len(data)):
        c1_high = float(data.iloc[i - 2]["high"])
        c3_low = float(data.iloc[i]["low"])
        c1_low = float(data.iloc[i - 2]["low"])
        c3_high = float(data.iloc[i]["high"])

        # Bullish FVG: candle 1 high < candle 3 low
        if c1_high < c3_low:
            gap = c3_low - c1_high
            if gap / c1_high > min_gap_pct:
                fvgs.append(PDArray(
                    array_type="fvg",
                    high=c3_low,
                    low=c1_high,
                    timeframe="htf",
                    created_at=data.index[i],
                ))

        # Bearish FVG: candle 3 high < candle 1 low
        if c3_high < c1_low:
            gap = c1_low - c3_high
            if gap / c1_low > min_gap_pct:
                fvgs.append(PDArray(
                    array_type="fvg",
                    high=c1_low,
                    low=c3_high,
                    timeframe="htf",
                    created_at=data.index[i],
                ))

    return fvgs


def detect_prior_highs_lows(
    daily_data: pd.DataFrame,
    lookback: int = 20,
) -> list[PDArray]:
    """Detect prior daily highs and lows as PD arrays."""
    arrays: list[PDArray] = []
    if len(daily_data) < lookback:
        return arrays

    recent = daily_data.iloc[-lookback:]
    high_idx = recent["high"].idxmax()
    low_idx = recent["low"].idxmin()

    high_val = float(recent.loc[high_idx, "high"])
    low_val = float(recent.loc[low_idx, "low"])

    arrays.append(PDArray("prior_high", high_val, high_val, "D1", high_idx))
    arrays.append(PDArray("prior_low", low_val, low_val, "D1", low_idx))

    return arrays


def check_proximity(
    price: float,
    arrays: list[PDArray],
    atr_value: float,
    proximity_mult: float = 1.0,
) -> PDArray | None:
    """Check if a price is within proximity of any unmitigated PD array."""
    threshold = atr_value * proximity_mult
    for arr in arrays:
        if arr.mitigated:
            continue
        mid = (arr.high + arr.low) / 2
        if abs(price - mid) <= threshold:
            return arr
    return None


def update_mitigation(arrays: list[PDArray], current_price: float) -> None:
    """Mark arrays as mitigated if price has traded through them."""
    for arr in arrays:
        if arr.mitigated:
            continue
        if arr.array_type == "fvg":
            if current_price >= arr.high or current_price <= arr.low:
                pass  # FVG mitigated when price fills the gap
            mid = (arr.high + arr.low) / 2
            if (current_price > arr.high and arr.low < current_price) or \
               (current_price < arr.low and arr.high > current_price):
                arr.mitigated = True
