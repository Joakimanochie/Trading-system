"""Quintuplets: 5 consecutive small same-colour candles."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, close_col: int = 3, high_col: int = 1, low_col: int = 2) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(4, len(data)):
        bodies = [abs(data[i-j, close_col] - data[i-j, open_col]) for j in range(5)]
        ranges = [data[i-j, high_col] - data[i-j, low_col] for j in range(5)]
        avg_range = np.mean(ranges) if np.mean(ranges) > 0 else 1
        all_small = all(b < avg_range * 0.5 for b in bodies)
        all_bull = all(data[i-j, close_col] > data[i-j, open_col] for j in range(5))
        all_bear = all(data[i-j, close_col] < data[i-j, open_col] for j in range(5))
        if all_small and all_bull:
            signals[i] = 1
        elif all_small and all_bear:
            signals[i] = -1
    return signals
