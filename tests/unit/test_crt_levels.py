"""Test CRT level calculations."""
from agents.crt.anchor import AnchorCandle
from agents.crt.levels import calculate_levels
from datetime import datetime

def _anchor():
    return AnchorCandle(datetime.now(), "EURUSD", "H4", 1.08000, 1.08500, 1.08000, 1.08300,
                        crt_high=1.08500, crt_low=1.08000, crt_eq=1.08250)

def test_long_levels():
    lv = calculate_levels(_anchor(), "LONG")
    assert round(lv.tp1, 5) == 1.08250
    assert round(lv.tp2, 5) == 1.08500
    assert lv.entry < lv.tp1 < lv.tp2
    assert lv.sl_conservative < lv.entry

def test_short_levels():
    lv = calculate_levels(_anchor(), "SHORT")
    assert round(lv.tp1, 5) == 1.08250
    assert round(lv.tp2, 5) == 1.08000
    assert lv.entry > lv.tp1 > lv.tp2
    assert lv.sl_conservative > lv.entry
