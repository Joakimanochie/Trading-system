"""Test timezone map."""
from datetime import datetime
from agents.crt.timezone_map import server_to_est, get_h4_boundaries_est

def test_server_to_est():
    server = datetime(2026, 1, 15, 12, 0)
    est = server_to_est(server, server_utc_offset=2)
    assert est.hour == 5

def test_h4_boundaries():
    boundaries = get_h4_boundaries_est(server_utc_offset=2)
    assert len(boundaries) == 6
    assert "Server 00:00" in boundaries[0]
