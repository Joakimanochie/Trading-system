"""Per-trade stop loss: percentage-based and ATR-based modes."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StopLossResult:
    mode: str
    stop_price: float
    distance: float
    distance_pct: float


def percentage_stop(entry_price: float, direction: str, pct: float = 0.02) -> StopLossResult:
    """Fixed percentage stop loss."""
    distance = entry_price * pct
    if direction == "LONG":
        stop = entry_price - distance
    else:
        stop = entry_price + distance
    return StopLossResult("percentage", round(stop, 6), round(distance, 6), pct)


def atr_stop(entry_price: float, direction: str, atr_value: float, multiplier: float = 2.0) -> StopLossResult:
    """ATR-based stop loss."""
    distance = atr_value * multiplier
    if direction == "LONG":
        stop = entry_price - distance
    else:
        stop = entry_price + distance
    pct = distance / entry_price if entry_price > 0 else 0
    return StopLossResult("atr", round(stop, 6), round(distance, 6), round(pct, 6))
