"""Integration test: mock MT5 data → CRT runner → signal detection."""
import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")
import pandas as pd
from datetime import datetime, timedelta
from agents.crt.runner import scan_pair

def _make_htf():
    dates = [datetime(2026,1,1)+timedelta(hours=4*i) for i in range(10)]
    return pd.DataFrame({
        "open": [1.08,1.082,1.081,1.083,1.079,1.082,1.084,1.083,1.085,1.084],
        "high": [1.085,1.084,1.083,1.085,1.084,1.086,1.087,1.086,1.088,1.087],
        "low":  [1.079,1.080,1.079,1.081,1.078,1.080,1.082,1.081,1.083,1.082],
        "close":[1.082,1.081,1.082,1.084,1.082,1.084,1.085,1.084,1.086,1.085],
    }, index=dates)

def _make_ltf():
    dates = [datetime(2026,1,1)+timedelta(minutes=5*i) for i in range(200)]
    return pd.DataFrame({
        "open": [1.082]*200, "high": [1.084]*200, "low": [1.080]*200, "close": [1.083]*200,
    }, index=dates)

def test_crt_pipeline_runs():
    result = scan_pair("EURUSD", _make_htf(), _make_ltf())
    # May or may not produce a signal depending on data — but should not crash
    assert result is None or hasattr(result, "direction")
