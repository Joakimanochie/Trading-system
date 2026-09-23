"""Slingshot: pullback into prior candle range then breakout."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(2, len(data)):
        c0, o0 = data[i-2, close_col], data[i-2, open_col]
        h1, l1 = data[i-1, high_col], data[i-1, low_col]
        h0, l0 = data[i-2, high_col], data[i-2, low_col]
        c2 = data[i, close_col]
        if c0 > o0 and l1 >= l0 and l1 <= c0 and c2 > h0:
            signals[i] = 1
        elif c0 < o0 and h1 <= h0 and h1 >= c0 and c2 < l0:
            signals[i] = -1
    return signals
