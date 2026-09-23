"""Stress test: verify risk limits pause strategies during crash scenarios."""
import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")
from agents.risk.limits import check_all
from agents.risk.dashboard import compute_risk_state

def test_2020_crash_triggers_pause():
    """Simulate a 30% drawdown — risk limits should trigger."""
    state = compute_risk_state(equity=70000, peak_equity=100000, daily_start_equity=85000,
                                total_position_value=200000, largest_position_value=50000)
    assert state.should_pause is True
    assert len(state.violations) >= 1

def test_daily_loss_halt():
    """Simulate a 5% daily loss — should breach 2% limit."""
    state = compute_risk_state(equity=95000, peak_equity=100000, daily_start_equity=100000,
                                total_position_value=100000, largest_position_value=30000)
    assert state.should_pause is True
    assert any("Daily loss" in v for v in state.violations)

def test_within_limits():
    """Normal conditions — no pause."""
    state = compute_risk_state(equity=99000, peak_equity=100000, daily_start_equity=99500,
                                total_position_value=100000, largest_position_value=15000)
    assert state.should_pause is False
