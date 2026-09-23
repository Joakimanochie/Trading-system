"""Test bias detection."""
import pandas as pd
from agents.backtesting.bias_checks import check_survivorship

def test_survivorship_short_data():
    data = pd.DataFrame({"close": range(100)}, index=pd.date_range("2024-01-01", periods=100))
    assert check_survivorship(data, "TEST") is False

def test_survivorship_ok():
    data = pd.DataFrame({"close": range(300)}, index=pd.date_range("2024-01-01", periods=300))
    assert check_survivorship(data, "TEST") is True
