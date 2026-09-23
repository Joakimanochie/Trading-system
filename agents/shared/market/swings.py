"""Fractal swing detection — shared by CRT MSS detector and Photon structure engine."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass
class SwingPoint:
    index: int
    timestamp: datetime
    price: float
    swing_type: str  # "high" or "low"


def detect_swings(
    data: pd.DataFrame,
    fractal_n: int = 2,
    high_col: str = "high",
    low_col: str = "low",
) -> list[SwingPoint]:
    """Detect fractal swing highs and lows.

    A swing high = bar whose high exceeds the highs of `fractal_n` bars on each side.
    Mirror for swing lows.
    """
    swings: list[SwingPoint] = []
    highs = data[high_col].values
    lows = data[low_col].values
    n = len(data)

    for i in range(fractal_n, n - fractal_n):
        # Swing high check
        is_swing_high = True
        for j in range(1, fractal_n + 1):
            if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                is_swing_high = False
                break
        if is_swing_high:
            swings.append(SwingPoint(
                index=i,
                timestamp=data.index[i],
                price=float(highs[i]),
                swing_type="high",
            ))

        # Swing low check
        is_swing_low = True
        for j in range(1, fractal_n + 1):
            if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                is_swing_low = False
                break
        if is_swing_low:
            swings.append(SwingPoint(
                index=i,
                timestamp=data.index[i],
                price=float(lows[i]),
                swing_type="low",
            ))

    swings.sort(key=lambda s: s.index)
    return swings


def label_structure(swings: list[SwingPoint]) -> list[tuple[SwingPoint, str]]:
    """Label swing points as HH/HL/LH/LL based on sequence."""
    if len(swings) < 2:
        return [(s, "UNKNOWN") for s in swings]

    labelled: list[tuple[SwingPoint, str]] = []
    last_high: float | None = None
    last_low: float | None = None

    for s in swings:
        if s.swing_type == "high":
            if last_high is None:
                label = "HH"
            elif s.price > last_high:
                label = "HH"
            else:
                label = "LH"
            last_high = s.price
        else:
            if last_low is None:
                label = "HL"
            elif s.price > last_low:
                label = "HL"
            else:
                label = "LL"
            last_low = s.price
        labelled.append((s, label))

    return labelled
