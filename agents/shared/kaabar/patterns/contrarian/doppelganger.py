"""Doppelganger: two consecutive candles with equal H/L, preceded by opposite-colour candle."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3, tolerance: float = 0.0002) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(2, len(data)):
        price_scale = max(abs(data[i, close_col]), 1)
        h_eq = abs(data[i, high_col] - data[i-1, high_col]) / price_scale < tolerance
        l_eq = abs(data[i, low_col] - data[i-1, low_col]) / price_scale < tolerance
        if h_eq and l_eq:
            if data[i-2, close_col] < data[i-2, open_col]:
                signals[i] = 1
            elif data[i-2, close_col] > data[i-2, open_col]:
                signals[i] = -1
    return signals
