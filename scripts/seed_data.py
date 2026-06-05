"""Seed the database with SPY, AAPL, MSFT OHLCV data from Yahoo Finance."""
from __future__ import annotations

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TICKERS = ["SPY", "AAPL", "MSFT"]
START = "2020-01-01"


if __name__ == "__main__":
    from data.ingestion.yahoo import fetch_ohlcv
    from data.pipeline import ingest_and_store

    for ticker in TICKERS:
        logger.info(f"Seeding {ticker}...")
        df = fetch_ohlcv(ticker, start=START)
        rows = ingest_and_store(ticker, "D1", df)
        logger.info(f"  → {rows} rows stored for {ticker}")

    logger.info("Seed complete.")
