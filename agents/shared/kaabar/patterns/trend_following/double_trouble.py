"""Double Trouble: two consecutive same-direction candles where C2 range > 2x prior ATR."""
from __future__ import annotations
import numpy as np
from agents.crt.kaabar.indicators import atr as calc_atr

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3, atr_lookback: int = 14) -> np.ndarray:
    d = data.copy()
    d = calc_atr(d, atr_lookback, high_col, low_col, close_col)
    atr_col = d.shape[1] - 1
    signals = np.zeros(len(d))
    for i in range(1, len(d)):
        c_prev, o_prev = d[i-1, close_col], d[i-1, open_col]
        c_curr, o_curr = d[i, close_col], d[i, open_col]
        rng = d[i, high_col] - d[i, low_col]
        atr_val = d[i, atr_col]
        if atr_val <= 0:
            continue
        if c_prev > o_prev and c_curr > o_curr and rng > 2 * atr_val:
            signals[i] = 1
        elif c_prev < o_prev and c_curr < o_curr and rng > 2 * atr_val:
            signals[i] = -1
    return signals
