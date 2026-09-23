"""Hammer / Shooting Star."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(len(data)):
        o, h, l, c = data[i, open_col], data[i, high_col], data[i, low_col], data[i, close_col]
        body = abs(c - o)
        total = h - l
        if total <= 0 or body <= 0:
            continue
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        if lower_wick > body * 2 and upper_wick < body * 0.5:
            signals[i] = 1
        elif upper_wick > body * 2 and lower_wick < body * 0.5:
            signals[i] = -1
    return signals
