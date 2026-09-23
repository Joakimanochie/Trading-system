"""Engulfing: current body fully engulfs prior body, opposite colour."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(1, len(data)):
        o0, c0 = data[i-1, open_col], data[i-1, close_col]
        o1, c1 = data[i, open_col], data[i, close_col]
        body0_top, body0_bot = max(o0, c0), min(o0, c0)
        body1_top, body1_bot = max(o1, c1), min(o1, c1)
        if c1 > o1 and c0 < o0 and body1_top > body0_top and body1_bot < body0_bot:
            signals[i] = 1
        elif c1 < o1 and c0 > o0 and body1_top > body0_top and body1_bot < body0_bot:
            signals[i] = -1
    return signals
