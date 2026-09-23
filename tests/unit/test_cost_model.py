"""Test cost model."""
from agents.backtesting.cost_model import CostModel

def test_total_bps():
    cm = CostModel(commission_bps=5, spread_bps=2, slippage_bps=2)
    assert cm.total_bps == 9.0

def test_total_pct():
    cm = CostModel(commission_bps=5, spread_bps=2, slippage_bps=2)
    assert cm.total_pct == 0.0009

def test_round_trip():
    cm = CostModel(commission_bps=5, spread_bps=2, slippage_bps=2)
    assert cm.round_trip_cost(100000) == 100000 * 0.0009 * 2
