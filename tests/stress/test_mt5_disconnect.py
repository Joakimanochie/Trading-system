"""Stress test: MT5 disconnect → watchdog pauses CRT agent."""
from agents.crt.mt5_watchdog import WatchdogState, run_watchdog_check
from unittest.mock import patch

def test_consecutive_failures_trigger_pause():
    state = WatchdogState(max_failures=2)

    with patch("agents.crt.mt5_watchdog.check_mt5_health", return_value=False), \
         patch("agents.crt.mt5_watchdog.restart_mt5_terminal", return_value=False), \
         patch("agents.crt.mt5_watchdog.pause_crt_agent"):

        state = run_watchdog_check(state)
        assert state.consecutive_failures == 1
        assert not state.paused

        state = run_watchdog_check(state)
        assert state.paused is True

def test_healthy_resets_failures():
    state = WatchdogState(consecutive_failures=1)
    with patch("agents.crt.mt5_watchdog.check_mt5_health", return_value=True):
        state = run_watchdog_check(state)
        assert state.consecutive_failures == 0
        assert state.healthy is True
