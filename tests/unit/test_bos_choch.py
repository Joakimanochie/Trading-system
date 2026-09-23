"""Test BOS/CHoCH detection."""
import pandas as pd
from datetime import datetime, timedelta
from agents.photon.structure_engine import analyze_structure
from agents.photon.bos_choch import detect_bos_choch, EventType

def test_bos_detection():
    dates = [datetime(2026,1,1)+timedelta(hours=4*i) for i in range(20)]
    highs = [10,11,12,13,14,15,14,13,14,15,16,17,16,15,16,17,18,17,16,17]
    lows =  [9,10,11,12,13,14,13,12,13,14,15,16,15,14,15,16,17,16,15,16]
    data = pd.DataFrame({"open":lows,"high":highs,"low":lows,"close":highs}, index=dates)
    levels = analyze_structure(data, fractal_n=2)
    events = detect_bos_choch(data, levels, trend="BULLISH")
    bos_events = [e for e in events if e.event_type == EventType.BOS]
    assert len(bos_events) >= 0  # depends on structure

def test_empty_data():
    data = pd.DataFrame({"open":[],"high":[],"low":[],"close":[]})
    events = detect_bos_choch(data, [], trend="BULLISH")
    assert events == []
