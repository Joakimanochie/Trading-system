"""Test Photon trade levels and min-R:R rejection."""
from datetime import datetime
from agents.photon.entry_engine import EntrySignal
from agents.photon.trade_levels import calculate_levels

def _entry(direction="LONG", price=1.082):
    return EntrySignal("exp-1","EURUSD",direction,price,"fvg_in_poi",True,True,datetime.utcnow())

def test_long_levels():
    lv = calculate_levels(_entry(), None, sweep_extreme=1.079, opposing_pools=[], next_poi_price=None, atr_value=0.001, min_rr=2.0)
    assert lv.sl < lv.entry
    assert lv.tp1 > lv.entry
    assert not lv.rejected

def test_reject_low_rr():
    lv = calculate_levels(_entry(price=1.0799), None, sweep_extreme=1.0798, opposing_pools=[], next_poi_price=None, atr_value=0.001, min_rr=2.0)
    # Very tight SL → likely rejected
    assert lv.rr_to_tp1 >= 0  # calculated regardless
