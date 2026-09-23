"""Test Kelly criterion formula."""
import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")
from agents.risk.kelly import kelly_fraction, fractional_kelly

def test_kelly_known_inputs():
    assert round(kelly_fraction(0.56, 7.63), 4) == 0.5023

def test_kelly_losing_strategy():
    assert kelly_fraction(0.3, 0.5) == 0.0

def test_kelly_zero_pf():
    assert kelly_fraction(0.5, 0) == 0.0

def test_fractional_kelly():
    full = kelly_fraction(0.56, 7.63)
    frac = fractional_kelly(0.56, 7.63, fraction=0.5)
    assert round(frac, 4) == round(full * 0.5, 4)
