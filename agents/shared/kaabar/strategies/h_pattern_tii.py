"""H Pattern confirmed by TII > 50 (bull) or < 50 (bear)."""
from __future__ import annotations
import numpy as np
from agents.crt.kaabar.patterns.trend_following.h_pattern import signal as hp_signal
from agents.crt.kaabar.indicators import trend_intensity_indicator as calc_tii

def signal(data: np.ndarray, open_col: int = 0, high_col: int = 1, low_col: int = 2, close_col: int = 3) -> np.ndarray:
    hp = hp_signal(data, open_col, high_col, low_col, close_col)
    d = data.copy()
    d = calc_tii(d, 20, close_col)
    tii_col = d.shape[1] - 1
    signals = np.zeros(len(data))
    for i in range(len(data)):
        if hp[i] == 1 and d[i, tii_col] > 50:
            signals[i] = 1
        elif hp[i] == -1 and d[i, tii_col] < 50:
            signals[i] = -1
    return signals
