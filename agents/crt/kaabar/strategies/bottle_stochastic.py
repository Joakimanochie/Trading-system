"""Bottle pattern confirmed by stochastic crossover."""
from __future__ import annotations
import numpy as np
from agents.crt.kaabar.patterns.trend_following.bottle import signal as bot_signal
from agents.crt.kaabar.indicators import stochastic as calc_stoch

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    bot = bot_signal(data, open_col, high_col, low_col, close_col)
    d = data.copy()
    d = calc_stoch(d, 14, high_col, low_col, close_col)
    stoch_col = d.shape[1] - 1
    signals = np.zeros(len(data))
    for i in range(1, len(data)):
        if bot[i] == 1 and d[i, stoch_col] > d[i-1, stoch_col] and d[i, stoch_col] < 30:
            signals[i] = 1
        elif bot[i] == -1 and d[i, stoch_col] < d[i-1, stoch_col] and d[i, stoch_col] > 70:
            signals[i] = -1
    return signals
