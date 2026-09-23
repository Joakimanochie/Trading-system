"""CRT Step 5: Calculate entry, SL, TP1, TP2 from anchor and sweep data."""
from __future__ import annotations

from dataclasses import dataclass

from agents.crt.anchor import AnchorCandle


@dataclass
class CRTLevels:
    entry: float
    sl_conservative: float
    sl_aggressive: float
    tp1: float  # EQ (50%)
    tp2: float  # opposite extreme


def calculate_levels(anchor: AnchorCandle, direction: str, entry_price: float | None = None) -> CRTLevels:
    """Calculate CRT trade levels.

    LONG: entry near sweep low, SL below CRT low, TP1 at EQ, TP2 at CRT high.
    SHORT: entry near sweep high, SL above CRT high, TP1 at EQ, TP2 at CRT low.
    """
    rng = anchor.crt_high - anchor.crt_low
    buffer = rng * 0.05

    if direction == "LONG":
        entry = entry_price or anchor.crt_low + buffer
        return CRTLevels(
            entry=entry,
            sl_conservative=anchor.crt_low - buffer * 2,
            sl_aggressive=anchor.crt_low,
            tp1=anchor.crt_eq,
            tp2=anchor.crt_high,
        )
    else:
        entry = entry_price or anchor.crt_high - buffer
        return CRTLevels(
            entry=entry,
            sl_conservative=anchor.crt_high + buffer * 2,
            sl_aggressive=anchor.crt_high,
            tp1=anchor.crt_eq,
            tp2=anchor.crt_low,
        )
