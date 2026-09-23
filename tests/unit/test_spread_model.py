"""Test spread model."""
from datetime import datetime
from agents.crt.spread_model import get_spread, is_in_session_open

def test_normal_spread():
    s = get_spread("EURUSD", datetime(2026,6,22,10,0))
    assert s.multiplier == 1.0
    assert not s.in_open_window

def test_open_window_spread():
    s = get_spread("EURUSD", datetime(2026,6,22,7,5))
    assert s.multiplier == 2.5
    assert s.in_open_window
    assert s.effective_spread_price > s.base_spread_price

def test_session_open_detection():
    assert is_in_session_open(datetime(2026,6,22,7,5)) is True
    assert is_in_session_open(datetime(2026,6,22,10,0)) is False
