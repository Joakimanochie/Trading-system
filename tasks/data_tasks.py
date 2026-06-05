"""Celery tasks for data pipeline operations."""
from __future__ import annotations

import logging

from tasks.celery_app import celery_app

logger = logging.getLogger("quant_os.tasks.data")


@celery_app.task(name="tasks.data_tasks.ingest_yahoo", bind=True, max_retries=3)
def ingest_yahoo(self, ticker: str, start_date: str, end_date: str | None = None):
    """Ingest OHLCV data from Yahoo Finance and store in DB."""
    try:
        from data.ingestion.yahoo import fetch_ohlcv
        from data.pipeline import ingest_and_store

        df = fetch_ohlcv(ticker, start_date, end_date)
        rows = ingest_and_store(ticker, "D1", df)
        logger.info(f"Ingested {rows} rows for {ticker}")
        return {"ticker": ticker, "rows": rows}
    except Exception as exc:
        logger.error(f"ingest_yahoo failed for {ticker}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.data_tasks.health_check")
def health_check():
    """Simple task to verify Celery worker is alive."""
    return {"status": "ok"}
