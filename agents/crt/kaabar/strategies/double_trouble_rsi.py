"""Double Trouble confirmed by RSI direction."""
from __future__ import annotations
import numpy as np
from agents.crt.kaabar.patterns.trend_following.double_trouble import signal as dt_signal
from agents.crt.kaabar.indicators import rsi as calc_rsi

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3, rsi_lookback: int = 14) -> np.ndarray:
    dt = dt_signal(data, open_col, high_col, low_col, close_col)
    d = data.copy()
    d = calc_rsi(d, rsi_lookback, close_col)
    rsi_col = d.shape[1] - 1
    signals = np.zeros(len(data))
    for i in range(1, len(data)):
        if dt[i] == 1 and d[i, rsi_col] > d[i-1, rsi_col]:
            signals[i] = 1
        elif dt[i] == -1 and d[i, rsi_col] < d[i-1, rsi_col]:
            signals[i] = -1
    return signals
