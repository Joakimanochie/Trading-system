"""Marubozu pattern: no-wick candle."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3, tolerance: float = 0.0001) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(len(data)):
        o, h, l, c = data[i, open_col], data[i, high_col], data[i, low_col], data[i, close_col]
        body = abs(c - o)
        if body < tolerance:
            continue
        if c > o and abs(h - c) < tolerance * body and abs(l - o) < tolerance * body:
            signals[i] = 1
        elif c < o and abs(h - o) < tolerance * body and abs(l - c) < tolerance * body:
            signals[i] = -1
    return signals
