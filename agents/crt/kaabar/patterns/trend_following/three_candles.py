"""Three White Soldiers / Three Black Crows."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(2, len(data)):
        c0, c1, c2 = data[i-2, close_col], data[i-1, close_col], data[i, close_col]
        o0, o1, o2 = data[i-2, open_col], data[i-1, open_col], data[i, open_col]
        if c0 > o0 and c1 > o1 and c2 > o2 and c1 > c0 and c2 > c1:
            signals[i] = 1
        elif c0 < o0 and c1 < o1 and c2 < o2 and c1 < c0 and c2 < c1:
            signals[i] = -1
    return signals
