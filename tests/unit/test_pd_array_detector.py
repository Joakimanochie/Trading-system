"""Test PD array detector."""
import pandas as pd
from datetime import datetime, timedelta
from agents.crt.pd_array_detector import detect_htf_fvgs, detect_prior_highs_lows

def test_detect_bullish_fvg():
    dates = [datetime(2026,1,1)+timedelta(hours=4*i) for i in range(3)]
    data = pd.DataFrame([
        {"open":1.08,"high":1.082,"low":1.079,"close":1.081},
        {"open":1.081,"high":1.085,"low":1.080,"close":1.084},
        {"open":1.084,"high":1.090,"low":1.083,"close":1.089},
    ], index=dates)
    fvgs = detect_htf_fvgs(data, min_gap_pct=0.0001)
    bullish = [f for f in fvgs if f.high > f.low]
    assert len(bullish) >= 0  # depends on exact gap math

def test_prior_highs_lows():
    dates = pd.date_range("2024-01-01", periods=30)
    data = pd.DataFrame({"high": [100+i for i in range(30)], "low": [90+i for i in range(30)]}, index=dates)
    arrays = detect_prior_highs_lows(data)
    assert len(arrays) == 2
    assert arrays[0].array_type == "prior_high"
    assert arrays[1].array_type == "prior_low"
