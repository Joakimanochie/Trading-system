"""CRT Signal Assembly: combine anchor, sweep, MSS, levels, filters, and Kaabar confluence."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

from agents.crt.anchor import AnchorCandle
from agents.crt.filters import CRTFilterResult
from agents.crt.levels import CRTLevels
from agents.crt.mss_detector import MSSResult

logger = logging.getLogger(__name__)

ALL_PATTERNS = {}

def _load_patterns() -> None:
    global ALL_PATTERNS
    if ALL_PATTERNS:
        return
    from agents.crt.kaabar.patterns.trend_following import (
        marubozu, three_candles, hikkake, double_trouble, h_pattern, bottle, slingshot, quintuplets,
    )
    from agents.crt.kaabar.patterns.contrarian import (
        engulfing, hammer, doji, harami, tweezers, piercing, inside_updown, doppelganger, mirror, barrier, euphoria, shrinking,
    )
    ALL_PATTERNS.update({
        "marubozu": marubozu, "three_candles": three_candles, "hikkake": hikkake,
        "double_trouble": double_trouble, "h_pattern": h_pattern, "bottle": bottle,
        "slingshot": slingshot, "quintuplets": quintuplets,
        "engulfing": engulfing, "hammer": hammer, "doji": doji, "harami": harami,
        "tweezers": tweezers, "piercing": piercing, "inside_updown": inside_updown,
        "doppelganger": doppelganger, "mirror": mirror, "barrier": barrier,
        "euphoria": euphoria, "shrinking": shrinking,
    })


@dataclass
class CRTSignalData:
    pair: str
    direction: str
    htf: str
    ltf: str
    anchor: AnchorCandle
    levels: CRTLevels
    filters: CRTFilterResult
    mss: MSSResult
    confluence_patterns: list[str] = field(default_factory=list)
    confluence_score: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


def compute_confluence(ltf_data: pd.DataFrame, direction: str) -> tuple[list[str], int]:
    """Run all Kaabar patterns on the last bar and return agreeing patterns."""
    _load_patterns()
    ohlc = ltf_data[["open", "high", "low", "close"]].values
    if len(ohlc) < 5:
        return [], 0

    agreeing: list[str] = []
    for name, mod in ALL_PATTERNS.items():
        try:
            signals = mod.signal(ohlc)
            last = signals[-1]
            if (direction == "LONG" and last == 1) or (direction == "SHORT" and last == -1):
                agreeing.append(name)
        except Exception:
            continue

    return agreeing, len(agreeing)


def build_signal(
    pair: str,
    direction: str,
    htf: str,
    ltf: str,
    anchor: AnchorCandle,
    levels: CRTLevels,
    filters: CRTFilterResult,
    mss: MSSResult,
    ltf_data: pd.DataFrame,
) -> CRTSignalData:
    """Assemble a complete CRT signal with confluence scoring."""
    patterns, score = compute_confluence(ltf_data, direction)
    return CRTSignalData(
        pair=pair,
        direction=direction,
        htf=htf,
        ltf=ltf,
        anchor=anchor,
        levels=levels,
        filters=filters,
        mss=mss,
        confluence_patterns=patterns,
        confluence_score=score,
    )
