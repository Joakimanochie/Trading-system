"""Barrier: 3-candle pattern using rounding to force equal highs or lows."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3, rounding: int = 4) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(2, len(data)):
        rh = [round(data[i-j, high_col], rounding) for j in range(3)]
        rl = [round(data[i-j, low_col], rounding) for j in range(3)]
        if rh[0] == rh[1] == rh[2]:
            if data[i, close_col] < data[i, open_col]:
                signals[i] = -1
        if rl[0] == rl[1] == rl[2]:
            if data[i, close_col] > data[i, open_col]:
                signals[i] = 1
    return signals
