"""Test live candle reconstruction."""
import pandas as pd
from datetime import datetime, timedelta
from agents.crt.live_candle import reconstruct_forming_candle, get_htf_open_time

def test_htf_open_time():
    assert get_htf_open_time(datetime(2026,6,22,14,35), "H4").hour == 12
    assert get_htf_open_time(datetime(2026,6,22,3,15), "H4").hour == 0

def test_reconstruct():
    base = datetime(2026,6,22,12,0)
    ltf = pd.DataFrame([
        {"open":1.08,"high":1.085,"low":1.079,"close":1.082},
        {"open":1.082,"high":1.090,"low":1.081,"close":1.088},
        {"open":1.088,"high":1.088,"low":1.084,"close":1.085},
    ], index=[base+timedelta(minutes=5*i) for i in range(3)])
    candle = reconstruct_forming_candle(ltf, "H4")
    assert candle is not None
    assert candle.high == 1.090
    assert candle.low == 1.079
    assert candle.close == 1.085
    assert candle.bar_count == 3
