"""Marubozu inside K's Volatility Bands middle line."""
from __future__ import annotations
import numpy as np
from agents.crt.kaabar.patterns.trend_following.marubozu import signal as mar_signal
from agents.crt.kaabar.indicators import k_volatility_band

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    mar = mar_signal(data, open_col, high_col, low_col, close_col)
    d = data.copy()
    d = k_volatility_band(d, 20, 2.0, high_col, low_col, close_col)
    mid_col = d.shape[1] - 3
    signals = np.zeros(len(data))
    for i in range(len(data)):
        if mar[i] == 1 and d[i, close_col] < d[i, mid_col]:
            signals[i] = 1
        elif mar[i] == -1 and d[i, close_col] > d[i, mid_col]:
            signals[i] = -1
    return signals
