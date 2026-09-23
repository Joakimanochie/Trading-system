"""Integration test: Photon pipeline runs without error on synthetic data."""
import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")
import pandas as pd
from datetime import datetime, timedelta
from agents.photon.structure_engine import analyze_structure
from agents.photon.bos_choch import detect_bos_choch
from agents.photon.trend_state import determine_trend

def _trending_data(n=50):
    import numpy as np
    np.random.seed(42)
    dates = [datetime(2026,1,1)+timedelta(hours=4*i) for i in range(n)]
    base = [100+i*0.3+np.random.normal(0,1) for i in range(n)]
    highs = [b+abs(np.random.normal(0,0.5)) for b in base]
    lows = [b-abs(np.random.normal(0,0.5)) for b in base]
    return pd.DataFrame({"open":lows,"high":highs,"low":lows,"close":base}, index=dates)

def test_photon_structure_and_trend():
    data = _trending_data()
    levels = analyze_structure(data)
    assert len(levels) > 0
    events = detect_bos_choch(data, levels, "BULLISH")
    trend = determine_trend(events, "H4", "narrative")
    assert trend.state.value in ("BULLISH", "BEARISH", "RANGING")
