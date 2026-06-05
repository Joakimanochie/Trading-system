"""Unit tests for data quality checker."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data.quality_checker import check_quality


def _make_clean_df(n: int = 50) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=n, freq="1D")
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    df = pd.DataFrame(
        {
            "open": close - 0.1,
            "high": close + 0.3,
            "low": close - 0.3,
            "close": close,
            "volume": np.random.randint(1000, 100000, n).astype(float),
        },
        index=dates,
    )
    return df


def test_clean_data_passes():
    df = _make_clean_df()
    report = check_quality(df, ticker="TEST", timeframe="D1")
    assert report.total_rows == 50
    assert report.is_clean


def test_zero_volume_flagged():
    df = _make_clean_df()
    df.iloc[5, df.columns.get_loc("volume")] = 0
    report = check_quality(df, ticker="TEST", timeframe="D1")
    assert report.zero_volume_rows >= 1
    assert not report.is_clean


def test_negative_price_flagged():
    df = _make_clean_df()
    df.iloc[3, df.columns.get_loc("close")] = -1.0
    report = check_quality(df, ticker="TEST", timeframe="D1")
    assert not report.is_clean


def test_high_less_than_low_flagged():
    df = _make_clean_df()
    df.iloc[10, df.columns.get_loc("high")] = df.iloc[10]["low"] - 1
    report = check_quality(df, ticker="TEST", timeframe="D1")
    assert not report.is_clean
