"""Photon Module 3: Per-TF trend state machine — BULLISH / BEARISH / RANGING."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agents.photon.bos_choch import StructureEvent, EventType


class TrendState(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGING = "RANGING"


@dataclass
class TFTrendState:
    timeframe: str
    state: TrendState
    last_event: StructureEvent | None = None
    role: str = ""  # perspective, narrative, bias, timing


def determine_trend(events: list[StructureEvent], timeframe: str, role: str = "") -> TFTrendState:
    """Determine trend state from the most recent structure events."""
    if not events:
        return TFTrendState(timeframe=timeframe, state=TrendState.RANGING, role=role)

    last = events[-1]

    if last.event_type == EventType.CHOCH:
        if last.level_broken.swing.swing_type == "high":
            state = TrendState.BULLISH
        else:
            state = TrendState.BEARISH
    elif last.event_type == EventType.BOS:
        if last.level_broken.swing.swing_type == "high":
            state = TrendState.BULLISH
        else:
            state = TrendState.BEARISH
    else:
        state = TrendState.RANGING

    return TFTrendState(timeframe=timeframe, state=state, last_event=last, role=role)


@dataclass
class MTFTrendView:
    perspective: TFTrendState  # D1
    narrative: TFTrendState    # H4
    bias: TFTrendState         # M15
    timing: TFTrendState       # M5/M1
