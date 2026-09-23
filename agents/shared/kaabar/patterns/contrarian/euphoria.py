"""Euphoria: gap-open candle in the opposite direction of prior trend."""
from __future__ import annotations
import numpy as np

def signal(data: np.ndarray, open_col: int = 0, close_col: int = 3) -> np.ndarray:
    signals = np.zeros(len(data))
    for i in range(1, len(data)):
        prev_bull = data[i-1, close_col] > data[i-1, open_col]
        gap_up = data[i, open_col] > data[i-1, close_col]
        gap_down = data[i, open_col] < data[i-1, close_col]
        curr_bear = data[i, close_col] < data[i, open_col]
        curr_bull = data[i, close_col] > data[i, open_col]
        if prev_bull and gap_up and curr_bear:
            signals[i] = -1
        elif not prev_bull and gap_down and curr_bull:
            signals[i] = 1
    return signals
