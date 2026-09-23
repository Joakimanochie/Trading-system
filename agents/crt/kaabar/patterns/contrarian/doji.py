"""Doji: close ~ open."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(1, len(data)):
        body = abs(data[i, close_col] - data[i, open_col])
        total = data[i, high_col] - data[i, low_col]
        if total > 0 and body / total < 0.1:
            if data[i-1, close_col] > data[i-1, open_col]:
                signals[i] = -1
            elif data[i-1, close_col] < data[i-1, open_col]:
                signals[i] = 1
    return signals
