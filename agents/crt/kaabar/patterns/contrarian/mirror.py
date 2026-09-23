"""Mirror: 4-candle reversal where first and last share same high or low."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3, tolerance: float = 0.0002) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(3, len(data)):
        price_scale = max(abs(data[i, close_col]), 1)
        if abs(data[i, low_col] - data[i-3, low_col]) / price_scale < tolerance:
            if data[i-3, close_col] < data[i-3, open_col] and data[i, close_col] > data[i, open_col]:
                signals[i] = 1
        if abs(data[i, high_col] - data[i-3, high_col]) / price_scale < tolerance:
            if data[i-3, close_col] > data[i-3, open_col] and data[i, close_col] < data[i, open_col]:
                signals[i] = -1
    return signals
