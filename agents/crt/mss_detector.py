"""CRT Step 4: Market Structure Shift (MSS) and Fair Value Gap (FVG) detection on LTF."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class MSSResult:
    detected: bool
    mss_timestamp: datetime | None = None
    fvg_high: float | None = None
    fvg_low: float | None = None
    displacement_size: float | None = None


def detect_mss(ltf_data: pd.DataFrame, direction: str, lookback: int = 20) -> MSSResult:
    """Scan LTF for a displacement candle breaking recent swing high/low.

    Also detect FVG: gap between the displacement candle body and adjacent candle.
    """
    if len(ltf_data) < lookback:
        return MSSResult(False)

    recent = ltf_data.iloc[-lookback:]
    highs = recent["high"].values
    lows = recent["low"].values
    closes = recent["close"].values
    opens = recent["open"].values

    for i in range(2, len(recent)):
        body = abs(float(closes[i]) - float(opens[i]))
        avg_body = sum(abs(float(closes[j]) - float(opens[j])) for j in range(max(0, i-5), i)) / min(i, 5)

        if avg_body == 0:
            continue
        is_displacement = body > avg_body * 1.5

        if not is_displacement:
            continue

        if direction == "LONG":
            swing_high = max(float(highs[j]) for j in range(max(0, i-5), i))
            if float(closes[i]) > swing_high:
                fvg_low = float(highs[i-1])
                fvg_high = float(lows[i])
                if fvg_high > fvg_low:
                    return MSSResult(
                        detected=True,
                        mss_timestamp=recent.index[i],
                        fvg_high=fvg_high,
                        fvg_low=fvg_low,
                        displacement_size=body,
                    )

        elif direction == "SHORT":
            swing_low = min(float(lows[j]) for j in range(max(0, i-5), i))
            if float(closes[i]) < swing_low:
                fvg_high = float(lows[i-1])
                fvg_low = float(highs[i])
                if fvg_high > fvg_low:
                    return MSSResult(
                        detected=True,
                        mss_timestamp=recent.index[i],
                        fvg_high=fvg_high,
                        fvg_low=fvg_low,
                        displacement_size=body,
                    )

    return MSSResult(False)
