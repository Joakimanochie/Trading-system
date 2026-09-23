"""Piercing line (bull) / Dark cloud cover (bear)."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(1, len(data)):
        o0, c0 = data[i-1, open_col], data[i-1, close_col]
        o1, c1 = data[i, open_col], data[i, close_col]
        mid0 = (o0 + c0) / 2
        if c0 < o0 and c1 > o1 and o1 < c0 and c1 > mid0 and c1 < o0:
            signals[i] = 1
        elif c0 > o0 and c1 < o1 and o1 > c0 and c1 < mid0 and c1 > o0:
            signals[i] = -1
    return signals
