"""ATR utility for shared use across agents."""
from __future__ import annotations

import pandas as pd


def compute_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range on a DataFrame with high/low/close columns."""
    high = data["high"]
    low = data["low"]
    close = data["close"]

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    return tr.rolling(window=period).mean()
