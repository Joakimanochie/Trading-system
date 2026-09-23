"""Tweezers: equal highs (bear) or equal lows (bull) across two candles."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, high_col: int = 1, low_col: int = 2, close_col: int = 3, open_col: int = 0, tolerance: float = 0.0002) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(1, len(data)):
        price_scale = max(abs(data[i, close_col]), 1)
        if abs(data[i, low_col] - data[i-1, low_col]) / price_scale < tolerance:
            if data[i-1, close_col] < data[i-1, open_col] and data[i, close_col] > data[i, open_col]:
                signals[i] = 1
        if abs(data[i, high_col] - data[i-1, high_col]) / price_scale < tolerance:
            if data[i-1, close_col] > data[i-1, open_col] and data[i, close_col] < data[i, open_col]:
                signals[i] = -1
    return signals
