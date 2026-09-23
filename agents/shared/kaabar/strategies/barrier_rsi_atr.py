"""Barrier pattern with RSI and ATR stop-loss."""
from __future__ import annotations
import numpy as np
from agents.crt.kaabar.patterns.contrarian.barrier import signal as bar_signal
from agents.crt.kaabar.indicators import rsi as calc_rsi, atr as calc_atr

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    bar = bar_signal(data, open_col, high_col, low_col, close_col)
    d = data.copy()
    d = calc_rsi(d, 14, close_col)
    rsi_col = d.shape[1] - 1
    signals = np.zeros(len(data))
    for i in range(len(data)):
        if bar[i] == 1 and d[i, rsi_col] < 40:
            signals[i] = 1
        elif bar[i] == -1 and d[i, rsi_col] > 60:
            signals[i] = -1
    return signals
