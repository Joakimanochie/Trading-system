"""Hikkake: false breakout inside bar pattern."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(3, len(data)):
        ih, il = data[i-2, high_col], data[i-2, low_col]
        oh, ol = data[i-3, high_col], data[i-3, low_col]
        if ih < oh and il > ol:
            if data[i-1, low_col] < il and data[i, close_col] > ih:
                signals[i] = 1
            elif data[i-1, high_col] > ih and data[i, close_col] < il:
                signals[i] = -1
    return signals
