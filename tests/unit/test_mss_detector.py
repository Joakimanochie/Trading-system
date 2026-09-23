"""Test MSS detector."""
import pandas as pd
from datetime import datetime, timedelta
from agents.crt.mss_detector import detect_mss

def test_no_mss_flat_data():
    dates = [datetime(2026,1,1)+timedelta(minutes=5*i) for i in range(30)]
    data = pd.DataFrame({"open":1.08,"high":1.081,"low":1.079,"close":1.08}, index=dates)
    result = detect_mss(data, "LONG")
    assert result.detected is False

def test_insufficient_data():
    dates = [datetime(2026,1,1)+timedelta(minutes=5*i) for i in range(5)]
    data = pd.DataFrame({"open":1.08,"high":1.081,"low":1.079,"close":1.08}, index=dates)
    result = detect_mss(data, "LONG", lookback=20)
    assert result.detected is False
