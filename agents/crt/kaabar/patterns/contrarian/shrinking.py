"""Shrinking: 5-candle pattern with diminishing body size then reversal."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(4, len(data)):
        bodies = [abs(data[i-j, close_col] - data[i-j, open_col]) for j in range(5)]
        shrinking = all(bodies[j] >= bodies[j+1] for j in range(3))  # bodies[0] is current
        if not shrinking:
            continue
        all_bear = all(data[i-j, close_col] < data[i-j, open_col] for j in range(1, 5))
        all_bull = all(data[i-j, close_col] > data[i-j, open_col] for j in range(1, 5))
        if all_bear and data[i, close_col] > data[i, open_col]:
            signals[i] = 1
        elif all_bull and data[i, close_col] < data[i, open_col]:
            signals[i] = -1
    return signals
