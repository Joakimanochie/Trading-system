"""Test EOF engine lifecycle."""
from datetime import datetime
from agents.photon.eof_engine import EOFEngine, ExpectationStatus

def test_full_lifecycle():
    eof = EOFEngine()
    exp = eof.create_expectation("EURUSD", "LONG", None, (1.080, 1.082))
    assert exp.status == ExpectationStatus.PENDING

    # Price not arrived yet
    assert eof.check_price_arrival(exp.id, 1.075, datetime.utcnow()) is False
    assert exp.status == ExpectationStatus.PENDING

    # Price arrives
    assert eof.check_price_arrival(exp.id, 1.081, datetime.utcnow()) is True
    assert exp.status == ExpectationStatus.PRICE_ARRIVED

    # Trigger
    eof.trigger(exp.id, datetime.utcnow())
    assert exp.status == ExpectationStatus.TRIGGERED

def test_expiry():
    eof = EOFEngine()
    exp = eof.create_expectation("GBPUSD", "SHORT", None, (1.260, 1.265))
    eof.expire(exp.id, "CHoCH invalidated premise")
    assert exp.status == ExpectationStatus.EXPIRED
    assert exp.expired_reason == "CHoCH invalidated premise"

def test_get_active():
    eof = EOFEngine()
    eof.create_expectation("EURUSD", "LONG", None, (1.08, 1.082))
    eof.create_expectation("GBPUSD", "SHORT", None, (1.26, 1.265))
    active = eof.get_active()
    assert len(active) == 2
    active_eur = eof.get_active("EURUSD")
    assert len(active_eur) == 1
