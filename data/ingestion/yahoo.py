"""Yahoo Finance OHLCV ingestion using yfinance."""
from __future__ import annotations

import logging
from datetime import date

import pandas as pd
import yfinance as yf

logger = logging.getLogger("quant_os.data.yahoo")


def fetch_ohlcv(
    ticker: str,
    start: str,
    end: str | None = None,
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance.

    Returns a DataFrame with columns: open, high, low, close, volume, ticker, timeframe.
    Index is a DatetimeIndex.
    """
    logger.info(f"Fetching {ticker} from Yahoo Finance [{start} → {end or 'today'}]")
    df = yf.download(ticker, start=start, end=end, interval=interval, progress=False, auto_adjust=True)

    if df.empty:
        raise ValueError(f"No data returned for {ticker} from Yahoo Finance")

    # Flatten multi-level columns if present (yfinance >=0.2.x multi-ticker download)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    df = df[["open", "high", "low", "close", "volume"]].copy()
    df.index.name = "timestamp"
    df["ticker"] = ticker
    df["timeframe"] = _interval_to_timeframe(interval)
    df = df.dropna(subset=["open", "high", "low", "close"])

    logger.info(f"Fetched {len(df)} rows for {ticker}")
    return df


def _interval_to_timeframe(interval: str) -> str:
    mapping = {
        "1m": "M1", "5m": "M5", "15m": "M15", "30m": "M30",
        "1h": "H1", "4h": "H4", "1d": "D1", "1wk": "W1", "1mo": "MN",
    }
    return mapping.get(interval, interval.upper())
