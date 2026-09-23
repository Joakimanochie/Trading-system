"""Test dealing range."""
import pandas as pd
from agents.crt.dealing_range import find_dealing_range, validate_premium_discount

def test_find_range():
    data = pd.DataFrame({"high": [110,115,112,118,114], "low": [100,105,102,108,104]},
                        index=pd.date_range("2024-01-01", periods=5))
    dr = find_dealing_range(data, lookback=5)
    assert dr is not None
    assert dr.swing_high == 118
    assert dr.swing_low == 100
    assert dr.eq_50 == 109

def test_premium_discount():
    data = pd.DataFrame({"high": [110,115,112,118,114], "low": [100,105,102,108,104]},
                        index=pd.date_range("2024-01-01", periods=5))
    dr = find_dealing_range(data, lookback=5)
    assert validate_premium_discount("LONG", 105, dr) is True
    assert validate_premium_discount("LONG", 115, dr) is False
    assert validate_premium_discount("SHORT", 115, dr) is True
