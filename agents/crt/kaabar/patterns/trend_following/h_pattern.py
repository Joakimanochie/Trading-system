"""H Pattern: trend candle -> doji -> confirmation candle."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(2, len(data)):
        o0, c0 = data[i-2, open_col], data[i-2, close_col]
        o1, h1, c1 = data[i-1, open_col], data[i-1, high_col], data[i-1, close_col]
        o2, l2, c2 = data[i, open_col], data[i, low_col], data[i, close_col]
        body1 = abs(c1 - o1)
        range1 = data[i-1, high_col] - data[i-1, low_col]
        is_doji = body1 < range1 * 0.1 if range1 > 0 else False
        if c0 > o0 and is_doji and h1 > data[i-2, high_col] and c2 > o2 and c2 > c1 and l2 > data[i-1, low_col]:
            signals[i] = 1
        elif c0 < o0 and is_doji and data[i-1, low_col] < data[i-2, low_col] and c2 < o2 and c2 < c1 and data[i, high_col] < h1:
            signals[i] = -1
    return signals
