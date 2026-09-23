"""K's Candlestick filter: current open = prior close condition."""
from __future__ import annotations
import numpy as np

def filter_signals(data: np.ndarray, signals: np.ndarray, open_col: int = 0, close_col: int = 3, tolerance: float = 0.0002) -> np.ndarray:
    filtered = signals.copy()
    for i in range(1, len(data)):
        price_scale = max(abs(data[i, close_col]), 1)
        if abs(data[i, open_col] - data[i-1, close_col]) / price_scale > tolerance:
            filtered[i] = 0
    return filtered
