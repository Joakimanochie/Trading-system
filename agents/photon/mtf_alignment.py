"""Photon Module 7: Multi-Timeframe Alignment checklist."""
from __future__ import annotations

from dataclasses import dataclass

from agents.photon.trend_state import TFTrendState, TrendState


@dataclass
class AlignmentResult:
    d1_aligned: bool
    h4_aligned: bool
    m15_aligned: bool
    ltf_aligned: bool
    score: int  # 0-4
    direction: str


def check_alignment(
    direction: str,
    d1: TFTrendState,
    h4: TFTrendState,
    m15: TFTrendState,
    ltf: TFTrendState,
    min_alignment: int = 3,
) -> AlignmentResult:
    """Check multi-timeframe alignment for a trade direction.

    D1 = perspective, H4 = narrative, M15 = bias, LTF = timing.
    Score 0-4; minimum 3 required by default (D1 may be neutral).
    """
    target = TrendState.BULLISH if direction == "LONG" else TrendState.BEARISH

    d1_ok = d1.state == target or d1.state == TrendState.RANGING
    h4_ok = h4.state == target
    m15_ok = m15.state == target
    ltf_ok = ltf.state == target

    score = sum([d1_ok, h4_ok, m15_ok, ltf_ok])

    return AlignmentResult(
        d1_aligned=d1_ok,
        h4_aligned=h4_ok,
        m15_aligned=m15_ok,
        ltf_aligned=ltf_ok,
        score=score,
        direction=direction,
    )
