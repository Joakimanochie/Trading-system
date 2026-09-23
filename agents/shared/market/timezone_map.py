"""Timezone mapping: broker server-time → EST conversion and H4 boundary verification.

MT5 brokers typically run on EET (UTC+2, UTC+3 DST). Session macros are defined in EST.
This module resolves the collision.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pytz

logger = logging.getLogger(__name__)

EST = pytz.timezone("US/Eastern")
EET = pytz.timezone("Europe/Athens")  # EET/EEST, matches most MT5 brokers


def detect_server_offset_hours(server_time: datetime, utc_now: datetime | None = None) -> int:
    """Auto-detect broker server UTC offset by comparing a server timestamp to UTC."""
    if utc_now is None:
        utc_now = datetime.now(timezone.utc)
    if server_time.tzinfo is None:
        diff = server_time - utc_now.replace(tzinfo=None)
    else:
        diff = server_time - utc_now
    return round(diff.total_seconds() / 3600)


def server_to_est(server_time: datetime, server_utc_offset: int = 2) -> datetime:
    """Convert a broker server timestamp to US/Eastern."""
    utc_time = server_time - timedelta(hours=server_utc_offset)
    utc_time = pytz.utc.localize(utc_time)
    return utc_time.astimezone(EST)


def server_to_utc(server_time: datetime, server_utc_offset: int = 2) -> datetime:
    """Convert a broker server timestamp to UTC."""
    utc_time = server_time - timedelta(hours=server_utc_offset)
    return pytz.utc.localize(utc_time)


def get_h4_boundaries_est(server_utc_offset: int = 2) -> list[str]:
    """Return H4 candle open times in EST for a given broker offset.

    H4 candles open at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 server time.
    """
    boundaries = []
    for hour in range(0, 24, 4):
        server_dt = datetime(2026, 1, 15, hour, 0, tzinfo=None)  # mid-January (no DST)
        est_dt = server_to_est(server_dt, server_utc_offset)
        boundaries.append(f"Server {hour:02d}:00 → EST {est_dt.strftime('%H:%M')}")
    return boundaries


def verify_h4_alignment(server_utc_offset: int = 2) -> dict:
    """Check if H4 boundaries align with key session opens in EST."""
    boundaries = get_h4_boundaries_est(server_utc_offset)
    session_opens = {"London": "03:00", "NY": "08:00", "Asian": "19:00"}

    est_opens = []
    for b in boundaries:
        est_time = b.split("EST ")[1]
        est_opens.append(est_time)

    alignment = {}
    for session, target in session_opens.items():
        aligned = target in est_opens
        alignment[session] = {"target": target, "aligned": aligned}

    logger.info("H4 boundaries in EST: %s", boundaries)
    logger.info("Session alignment: %s", alignment)
    return {"boundaries": boundaries, "alignment": alignment}
