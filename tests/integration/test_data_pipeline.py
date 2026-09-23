"""Integration test: ingest → store → query."""
import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")

def test_ohlcv_roundtrip():
    from db import SessionLocal
    from db.models import OHLCV
    db = SessionLocal()
    count = db.query(OHLCV).filter(OHLCV.ticker == "SPY").count()
    assert count > 0
    row = db.query(OHLCV).filter(OHLCV.ticker == "SPY").first()
    assert row.open > 0
    assert row.close > 0
    db.close()
