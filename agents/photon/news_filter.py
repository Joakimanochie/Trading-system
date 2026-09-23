"""Photon Module 10: News Filter — block entries near high-impact events."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class NewsEvent:
    name: str
    utc_time: datetime
    currency: str
    impact: str  # "high", "medium", "low"


# v1: manual schedule — replace with automated calendar feed in v2
WEEKLY_NEWS_SCHEDULE: list[dict] = []


def is_in_blackout(
    utc_now: datetime,
    events: list[NewsEvent] | None = None,
    blackout_mins: int = 15,
) -> tuple[bool, NewsEvent | None]:
    """Check if the current time is within a news blackout window."""
    if events is None:
        events = []

    for event in events:
        if event.impact != "high":
            continue
        window_start = event.utc_time - timedelta(minutes=blackout_mins)
        window_end = event.utc_time + timedelta(minutes=blackout_mins)
        if window_start <= utc_now <= window_end:
            return True, event

    return False, None


def load_news_schedule() -> list[NewsEvent]:
    """Load news events from config. v1 = manual; v2 = automated feed."""
    return [NewsEvent(**e) for e in WEEKLY_NEWS_SCHEDULE if all(k in e for k in ("name", "utc_time", "currency", "impact"))]
