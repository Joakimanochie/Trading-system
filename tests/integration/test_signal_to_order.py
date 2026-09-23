"""Integration test: signal → risk check → mock broker order."""
import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")
from unittest.mock import MagicMock, patch
from orchestrator.signal_router import route_signal

def test_signal_routed_to_approval():
    routed = route_signal("sig-1", "crt_agent", "EURUSD", "LONG", 1.082, 1.080, 1.086,
                           capital=100000, win_rate=0.56, profit_factor=7.63)
    assert routed.routed_to == "approval_queue"
    assert routed.position_size > 0

def test_signal_rejected_by_risk():
    routed = route_signal("sig-2", "crt_agent", "GBPUSD", "SHORT", 1.264, 1.266, 1.260,
                           current_drawdown=0.20)
    assert routed.routed_to == "rejected"
    assert len(routed.risk_violations) > 0
