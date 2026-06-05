"""Data quality checks: price gaps, zero-volume days, outlier detection."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

logger = logging.getLogger("quant_os.data.quality")


@dataclass
class QualityReport:
    ticker: str
    timeframe: str
    total_rows: int
    zero_volume_rows: int
    price_gap_rows: int
    outlier_rows: int
    issues: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0


def check_quality(df: pd.DataFrame, ticker: str = "", timeframe: str = "") -> QualityReport:
    """
    Run quality checks on an OHLCV DataFrame.

    Expects columns: open, high, low, close, volume (volume optional).
    """
    report = QualityReport(
        ticker=ticker,
        timeframe=timeframe,
        total_rows=len(df),
        zero_volume_rows=0,
        price_gap_rows=0,
        outlier_rows=0,
    )

    if df.empty:
        report.issues.append("DataFrame is empty")
        return report

    # Zero-volume days
    if "volume" in df.columns:
        zero_vol = (df["volume"] == 0).sum()
        report.zero_volume_rows = int(zero_vol)
        if zero_vol > 0:
            report.issues.append(f"{zero_vol} zero-volume rows")

    # Price gaps: close-to-open gap > 10% of close price
    if "close" in df.columns and "open" in df.columns and len(df) > 1:
        gaps = (df["open"].shift(-1) - df["close"]).abs() / df["close"]
        gap_rows = int((gaps > 0.10).sum())
        report.price_gap_rows = gap_rows
        if gap_rows > 0:
            report.issues.append(f"{gap_rows} price gaps > 10%")

    # Outlier prices: close price > 5-sigma from rolling mean
    if "close" in df.columns and len(df) > 30:
        rolling_mean = df["close"].rolling(window=30, min_periods=10).mean()
        rolling_std = df["close"].rolling(window=30, min_periods=10).std()
        z_scores = (df["close"] - rolling_mean).abs() / rolling_std.replace(0, np.nan)
        outliers = int((z_scores > 5).sum())
        report.outlier_rows = outliers
        if outliers > 0:
            report.issues.append(f"{outliers} outlier prices (>5-sigma)")

    # Negative prices
    price_cols = [c for c in ["open", "high", "low", "close"] if c in df.columns]
    for col in price_cols:
        neg = int((df[col] <= 0).sum())
        if neg > 0:
            report.issues.append(f"{neg} non-positive values in {col}")

    # OHLC integrity: high >= low, high >= open, high >= close
    if all(c in df.columns for c in ["open", "high", "low", "close"]):
        bad_hl = int((df["high"] < df["low"]).sum())
        if bad_hl:
            report.issues.append(f"{bad_hl} rows where high < low")

    if report.issues:
        logger.warning(f"Quality issues for {ticker}/{timeframe}: {report.issues}")
    else:
        logger.debug(f"Quality check passed for {ticker}/{timeframe} — {len(df)} rows")

    return report
