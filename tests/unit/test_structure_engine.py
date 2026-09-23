"""Test Photon structure engine."""
import pandas as pd
from datetime import datetime, timedelta
from agents.photon.structure_engine import analyze_structure

def test_swing_detection():
    dates = [datetime(2026,1,1)+timedelta(hours=4*i) for i in range(20)]
    highs = [10,11,12,11,10,9,8,9,10,11,12,13,12,11,10,9,10,11,12,11]
    lows =  [9,10,11,10,9,8,7,8,9,10,11,12,11,10,9,8,9,10,11,10]
    data = pd.DataFrame({"open":lows,"high":highs,"low":lows,"close":highs}, index=dates)
    levels = analyze_structure(data, fractal_n=2)
    assert len(levels) > 0
    labels = [l.label for l in levels]
    assert any(l in ("HH","HL","LH","LL") for l in labels)

def test_strong_weak():
    dates = [datetime(2026,1,1)+timedelta(hours=4*i) for i in range(20)]
    highs = [10,11,12,11,10,9,8,9,10,11,12,13,12,11,10,9,10,11,12,11]
    lows =  [9,10,11,10,9,8,7,8,9,10,11,12,11,10,9,8,9,10,11,10]
    data = pd.DataFrame({"open":lows,"high":highs,"low":lows,"close":highs}, index=dates)
    levels = analyze_structure(data, fractal_n=2)
    strong_count = sum(1 for l in levels if l.strong)
    weak_count = sum(1 for l in levels if not l.strong)
    assert strong_count + weak_count == len(levels)
