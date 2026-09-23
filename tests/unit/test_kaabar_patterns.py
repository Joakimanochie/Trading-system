"""Test Kaabar pattern signal functions."""
import numpy as np
from agents.crt.kaabar.patterns.contrarian.engulfing import signal as contrarian_engulfing

def test_bullish_engulfing():
    data = np.array([
        [1.080, 1.082, 1.078, 1.079],  # bearish
        [1.077, 1.084, 1.076, 1.083],  # bullish engulfs
    ])
    signals = contrarian_engulfing(data)
    assert signals[1] == 1

def test_no_engulfing():
    data = np.array([
        [1.080, 1.082, 1.078, 1.079],
        [1.079, 1.080, 1.078, 1.079],  # no engulf
    ])
    signals = contrarian_engulfing(data)
    assert signals[1] == 0
