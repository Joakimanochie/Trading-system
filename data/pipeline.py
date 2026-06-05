"""Data pipeline: ingest → validate → store. Idempotent re-runs."""
from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from data.quality_checker import QualityReport, check_quality
from db import SessionLocal

logger = logging.getLogger("quant_os.data.pipeline")

# Raw OHLCV table name (time-series, not in ORM models — kept separate for performance)
_OHLCV_TABLE = "ohlcv"

_CREATE_OHLCV_TABLE = f"""
CREATE TABLE IF NOT EXISTS {_OHLCV_TABLE} (
    id          BIGSERIAL PRIMARY KEY,
    ticker      VARCHAR(20)  NOT NULL,
    timeframe   VARCHAR(10)  NOT NULL,
    timestamp   TIMESTAMPTZ  NOT NULL,
    open        DOUBLE PRECISION NOT NULL,
    high        DOUBLE PRECISION NOT NULL,
    low         DOUBLE PRECISION NOT NULL,
    close       DOUBLE PRECISION NOT NULL,
    volume      DOUBLE PRECISION,
    UNIQUE (ticker, timeframe, timestamp)
);
CREATE INDEX IF NOT EXISTS ix_ohlcv_ticker_tf_ts
    ON {_OHLCV_TABLE} (ticker, timeframe, timestamp);
"""


def ensure_ohlcv_table(db: Session) -> None:
    """Create the ohlcv table if it does not exist."""
    db.execute(text(_CREATE_OHLCV_TABLE))
    db.commit()


def ingest_and_store(
    ticker: str,
    timeframe: str,
    df: pd.DataFrame,
    run_quality_check: bool = True,
) -> int:
    """
    Validate and upsert OHLCV rows into the database.

    Returns the number of rows inserted/updated.
    """
    if df.empty:
        logger.warning(f"Empty DataFrame for {ticker}/{timeframe} — nothing to store")
        return 0

    if run_quality_check:
        report: QualityReport = check_quality(df, ticker=ticker, timeframe=timeframe)
        if not report.is_clean:
            logger.warning(
                f"Quality issues for {ticker}/{timeframe}: {report.issues}. Proceeding anyway."
            )

    # Normalise column names
    df = df.copy()
    df.index.name = "timestamp"
    df = df.reset_index()
    df["ticker"] = ticker
    df["timeframe"] = timeframe

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close", "timestamp"])

    rows_to_insert = df[["ticker", "timeframe", "timestamp", "open", "high", "low", "close", "volume"]].to_dict(
        orient="records"
    )

    upsert_sql = text(
        f"""
        INSERT INTO {_OHLCV_TABLE} (ticker, timeframe, timestamp, open, high, low, close, volume)
        VALUES (:ticker, :timeframe, :timestamp, :open, :high, :low, :close, :volume)
        ON CONFLICT (ticker, timeframe, timestamp) DO UPDATE SET
            open   = EXCLUDED.open,
            high   = EXCLUDED.high,
            low    = EXCLUDED.low,
            close  = EXCLUDED.close,
            volume = EXCLUDED.volume
        """
    )

    with SessionLocal() as db:
        ensure_ohlcv_table(db)
        db.execute(upsert_sql, rows_to_insert)
        db.commit()

    logger.info(f"Stored {len(rows_to_insert)} rows for {ticker}/{timeframe}")
    return len(rows_to_insert)


def query_ohlcv(
    ticker: str,
    timeframe: str,
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Query OHLCV data from the database and return a DataFrame."""
    conditions = ["ticker = :ticker", "timeframe = :timeframe"]
    params: dict = {"ticker": ticker, "timeframe": timeframe}

    if start:
        conditions.append("timestamp >= :start")
        params["start"] = start
    if end:
        conditions.append("timestamp <= :end")
        params["end"] = end

    where_clause = " AND ".join(conditions)
    limit_clause = f"LIMIT {limit}" if limit else ""

    sql = text(
        f"SELECT * FROM {_OHLCV_TABLE} WHERE {where_clause} ORDER BY timestamp ASC {limit_clause}"
    )

    with SessionLocal() as db:
        result = db.execute(sql, params)
        rows = result.fetchall()
        cols = result.keys()

    return pd.DataFrame(rows, columns=list(cols))
