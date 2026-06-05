"""Unit tests for Settings config loading."""
from __future__ import annotations

import os

import pytest


def test_settings_loads_defaults():
    from config import Settings
    s = Settings()
    assert s.api_port == 8000
    assert s.execution_mode == "MANUAL"
    assert s.risk_kelly_fraction == 0.50


def test_crt_pairs_list():
    from config import Settings
    s = Settings(crt_pairs="EURUSD,GBPUSD,XAUUSD")
    assert s.crt_pairs_list == ["EURUSD", "GBPUSD", "XAUUSD"]


def test_cors_origins_list():
    from config import Settings
    s = Settings(cors_origins="http://localhost:3000,http://localhost:5173")
    assert "http://localhost:3000" in s.cors_origins_list
