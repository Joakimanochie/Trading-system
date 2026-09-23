"""Harami: current body inside prior body."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(1, len(data)):
        top0 = max(data[i-1, open_col], data[i-1, close_col])
        bot0 = min(data[i-1, open_col], data[i-1, close_col])
        top1 = max(data[i, open_col], data[i, close_col])
        bot1 = min(data[i, open_col], data[i, close_col])
        if top1 < top0 and bot1 > bot0:
            if data[i-1, close_col] < data[i-1, open_col] and data[i, close_col] > data[i, open_col]:
                signals[i] = 1
            elif data[i-1, close_col] > data[i-1, open_col] and data[i, close_col] < data[i, open_col]:
                signals[i] = -1
    return signals
