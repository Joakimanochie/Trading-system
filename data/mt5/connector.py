"""
MT5 Python library wrapper.
Implements get_quotes() and mass_import() exactly as described in Kaabar Ch1.
MetaTrader5 is Windows-only; on other platforms MT5_ENABLED should be false.
"""
from __future__ import annotations

import datetime
import logging

import numpy as np
import pandas as pd
import pytz

logger = logging.getLogger("quant_os.data.mt5")


def get_quotes(time_frame: int, year: int, month: int, day: int, asset: str) -> pd.DataFrame:
    """
    Pull historical OHLCV from MT5 for a given asset and timeframe.
    Exact implementation from Kaabar Ch1.
    """
    import MetaTrader5 as mt5  # type: ignore[import]

    if not mt5.initialize():
        raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

    timezone = pytz.timezone("Europe/Paris")
    time_from = datetime.datetime(year, month, day, tzinfo=timezone)
    time_to = datetime.datetime.now(timezone) + datetime.timedelta(days=1)
    rates = mt5.copy_rates_range(asset, time_frame, time_from, time_to)

    if rates is None or len(rates) == 0:
        logger.warning(f"No data returned from MT5 for {asset}")
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.rename(columns={"time": "timestamp"})
    return df


def mass_import(asset: str, time_frame: str, from_year: int = 2020) -> np.ndarray:
    """
    Pull OHLC array for any pair + timeframe.
    Returns numpy array with columns: open, high, low, close.
    Exact implementation from Kaabar Ch1.
    """
    from data.mt5.timeframes import resolve_timeframe

    tf_const = resolve_timeframe(time_frame)
    df = get_quotes(tf_const, from_year, 1, 1, asset=asset)

    if df.empty:
        raise RuntimeError(f"mass_import: no data for {asset}/{time_frame}")

    # Columns 1:5 = open, high, low, close (index 0 = timestamp)
    ohlc_cols = ["open", "high", "low", "close"]
    available = [c for c in ohlc_cols if c in df.columns]
    if not available:
        # Fall back to positional (raw rates structure)
        data = df.iloc[:, 1:5].values.round(decimals=5)
    else:
        data = df[available].values.round(decimals=5)

    logger.info(f"mass_import: {asset}/{time_frame} → {data.shape[0]} candles")
    return data


def initialize_mt5(login: int | None = None, password: str | None = None, server: str | None = None) -> bool:
    """
    Initialize MT5 connection with optional credentials.
    Falls back to already-open MT5 terminal if no credentials provided.
    """
    import MetaTrader5 as mt5  # type: ignore[import]

    if login and password and server:
        result = mt5.initialize(login=login, password=password, server=server)
    else:
        result = mt5.initialize()

    if not result:
        logger.error(f"MT5 initialization failed: {mt5.last_error()}")
        return False

    info = mt5.terminal_info()
    logger.info(f"MT5 connected — build {info.build}, connected={info.connected}")
    return True


def shutdown_mt5() -> None:
    import MetaTrader5 as mt5  # type: ignore[import]
    mt5.shutdown()
    logger.info("MT5 connection closed")
