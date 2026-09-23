"""Photon Module 2: BOS / CHoCH Detector."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import pandas as pd

from agents.photon.structure_engine import StructureLevel


class EventType(str, Enum):
    BOS = "BOS"      # Break of Structure — with-trend continuation
    CHOCH = "CHoCH"  # Change of Character — first counter-trend break


@dataclass
class StructureEvent:
    event_type: EventType
    level_broken: StructureLevel
    break_price: float
    break_timestamp: datetime
    confirm_mode: str  # "close" or "wick"


def detect_bos_choch(
    data: pd.DataFrame,
    levels: list[StructureLevel],
    trend: str = "BULLISH",
    confirm_mode: str = "close",
) -> list[StructureEvent]:
    """Detect BOS and CHoCH events from price breaking structure levels.

    BOS = break in the SAME direction as trend (continuation).
    CHoCH = FIRST break AGAINST the current trend (bias warning).
    """
    events: list[StructureEvent] = []
    broken_levels: set[int] = set()
    had_choch = False

    for i in range(len(data)):
        price_high = float(data.iloc[i]["high"])
        price_low = float(data.iloc[i]["low"])
        price_close = float(data.iloc[i]["close"])

        for level in levels:
            if id(level) in broken_levels:
                continue
            if level.swing.index >= i:
                continue

            break_price = price_close if confirm_mode == "close" else (price_high if level.swing.swing_type == "high" else price_low)

            if level.swing.swing_type == "high" and break_price > level.swing.price:
                if trend == "BULLISH":
                    event_type = EventType.BOS
                else:
                    event_type = EventType.CHOCH if not had_choch else EventType.BOS
                    if event_type == EventType.CHOCH:
                        had_choch = True

                events.append(StructureEvent(
                    event_type=event_type,
                    level_broken=level,
                    break_price=break_price,
                    break_timestamp=data.index[i],
                    confirm_mode=confirm_mode,
                ))
                broken_levels.add(id(level))

            elif level.swing.swing_type == "low" and break_price < level.swing.price:
                if trend == "BEARISH":
                    event_type = EventType.BOS
                else:
                    event_type = EventType.CHOCH if not had_choch else EventType.BOS
                    if event_type == EventType.CHOCH:
                        had_choch = True

                events.append(StructureEvent(
                    event_type=event_type,
                    level_broken=level,
                    break_price=break_price,
                    break_timestamp=data.index[i],
                    confirm_mode=confirm_mode,
                ))
                broken_levels.add(id(level))

    return events
