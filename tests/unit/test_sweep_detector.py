"""Test sweep detection."""
import pandas as pd
from datetime import datetime, timedelta
from agents.crt.anchor import AnchorCandle
from agents.crt.sweep_detector import detect_sweep, SweepType

def _make_htf(candles):
    dates = [datetime(2026,1,1) + timedelta(hours=4*i) for i in range(len(candles))]
    return pd.DataFrame(candles, index=dates, columns=["open","high","low","close"])

def test_bullish_sweep():
    anchor = AnchorCandle(datetime(2026,1,1), "TEST", "H4", 1.08, 1.085, 1.080, 1.083,
                          crt_high=1.085, crt_low=1.080, crt_eq=1.0825)
    htf = _make_htf([
        [1.080, 1.085, 1.080, 1.083],
        [1.082, 1.083, 1.079, 1.081],  # sweeps low, closes above
    ])
    result = detect_sweep(htf, anchor)
    assert result.sweep_type == SweepType.SWEEP_LOW
    assert result.direction == "LONG"

def test_no_sweep():
    anchor = AnchorCandle(datetime(2026,1,1), "TEST", "H4", 1.08, 1.085, 1.080, 1.083,
                          crt_high=1.085, crt_low=1.080, crt_eq=1.0825)
    htf = _make_htf([
        [1.080, 1.085, 1.080, 1.083],
        [1.082, 1.084, 1.081, 1.083],  # stays inside range
    ])
    result = detect_sweep(htf, anchor)
    assert result.sweep_type == SweepType.NONE
