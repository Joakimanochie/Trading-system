"""Session clock: determine if current time falls within a key macro session window."""
from __future__ import annotations

from datetime import datetime, time

import pytz


FOREX_SESSIONS = {
    "london_open": (time(7, 0), time(10, 0)),
    "london_close": (time(14, 0), time(17, 0)),
    "new_york_open": (time(12, 0), time(15, 0)),
    "new_york_close": (time(19, 0), time(22, 0)),
    "asian_open": (time(0, 0), time(3, 0)),
    "asian_close": (time(6, 0), time(9, 0)),
}

FUTURES_SESSIONS = {
    "cme_open": (time(13, 30), time(14, 30)),
    "cme_close": (time(20, 0), time(21, 0)),
}


def is_in_session(utc_now: datetime | None = None, session_type: str = "forex") -> bool:
    """Check if the current UTC time falls within any macro session window."""
    if utc_now is None:
        utc_now = datetime.now(pytz.utc)
    elif utc_now.tzinfo is None:
        utc_now = pytz.utc.localize(utc_now)

    current_time = utc_now.time()
    sessions = FOREX_SESSIONS if session_type == "forex" else FUTURES_SESSIONS

    for name, (start, end) in sessions.items():
        if start <= current_time <= end:
            return True
    return False


def get_active_sessions(utc_now: datetime | None = None) -> list[str]:
    """Return list of currently active session names."""
    if utc_now is None:
        utc_now = datetime.now(pytz.utc)
    elif utc_now.tzinfo is None:
        utc_now = pytz.utc.localize(utc_now)

    current_time = utc_now.time()
    active = []
    for name, (start, end) in {**FOREX_SESSIONS, **FUTURES_SESSIONS}.items():
        if start <= current_time <= end:
            active.append(name)
    return active
