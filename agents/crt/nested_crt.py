"""CRT Step 3: Nested CRT — detect micro sweep on LTF around the sweep zone."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class NestedCRTResult:
    detected: bool
    micro_high: float | None = None
    micro_low: float | None = None
    sweep_idx: int | None = None


def detect_nested_crt(
    ltf_data: pd.DataFrame,
    sweep_zone_high: float,
    sweep_zone_low: float,
    direction: str,
    lookback: int = 10,
) -> NestedCRTResult:
    """On LTF, find a micro anchor range around the sweep zone and detect a nested sweep."""
    if len(ltf_data) < lookback:
        return NestedCRTResult(False)

    recent = ltf_data.iloc[-lookback:]
    micro_high = float(recent["high"].max())
    micro_low = float(recent["low"].min())

    for i in range(len(recent) - 1, 0, -1):
        candle = recent.iloc[i]
        h, l, c = float(candle["high"]), float(candle["low"]), float(candle["close"])

        if direction == "LONG" and l < micro_low and c > micro_low:
            return NestedCRTResult(True, micro_high, micro_low, i)
        if direction == "SHORT" and h > micro_high and c < micro_high:
            return NestedCRTResult(True, micro_high, micro_low, i)

    return NestedCRTResult(False, micro_high, micro_low)
