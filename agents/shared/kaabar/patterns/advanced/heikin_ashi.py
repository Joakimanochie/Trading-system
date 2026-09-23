"""Heikin-Ashi conversion and pattern detection on smoothed data."""
from __future__ import annotations
import numpy as np

def convert_to_heikin_ashi(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    ha = data.copy()
    ha[0, close_col] = (data[0, open_col] + data[0, high_col] + data[0, low_col] + data[0, close_col]) / 4
    ha[0, open_col] = (data[0, open_col] + data[0, close_col]) / 2
    for i in range(1, len(data)):
        ha[i, close_col] = (data[i, open_col] + data[i, high_col] + data[i, low_col] + data[i, close_col]) / 4
        ha[i, open_col] = (ha[i-1, open_col] + ha[i-1, close_col]) / 2
        ha[i, high_col] = max(data[i, high_col], ha[i, open_col], ha[i, close_col])
        ha[i, low_col] = min(data[i, low_col], ha[i, open_col], ha[i, close_col])
    return ha
