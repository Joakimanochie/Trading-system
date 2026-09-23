"""Photon Module 4: Point of Interest (POI) detector — supply/demand zones."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from agents.shared.market.atr import compute_atr
from agents.shared.market.fvg import detect_fvgs, FVG
from agents.photon.structure_engine import StructureLevel


@dataclass
class POI:
    zone_high: float
    zone_low: float
    timeframe: str
    direction: str  # "demand" (bullish) or "supply" (bearish)
    created_at: datetime
    anchor_level: StructureLevel | None = None
    embedded_fvg: FVG | None = None
    fresh: bool = True
    mitigated: bool = False
    base_candles: int = 0


def detect_pois(
    data: pd.DataFrame,
    levels: list[StructureLevel],
    timeframe: str,
    departure_atr_mult: float = 1.5,
    max_base_candles: int = 5,
    fresh_only: bool = True,
    fvg_min_atr_mult: float = 0.25,
) -> list[POI]:
    """Detect qualified POIs (supply/demand zones).

    A zone qualifies only if ALL criteria pass:
    1. Impulsive departure from the zone
    2. Compact base (≤ max_base_candles)
    3. Fresh (untested)
    4. Anchored at a Strong level
    5. Optionally has an embedded FVG
    """
    atr_series = compute_atr(data)
    fvgs = detect_fvgs(data, atr_value=float(atr_series.iloc[-1]) if len(atr_series) > 0 else 0, min_atr_mult=fvg_min_atr_mult)

    pois: list[POI] = []
    strong_levels = [l for l in levels if l.strong]

    for level in strong_levels:
        idx = level.swing.index
        if idx >= len(data) - 2:
            continue

        atr_val = float(atr_series.iloc[idx]) if idx < len(atr_series) and not pd.isna(atr_series.iloc[idx]) else 0

        # Check departure: candle after the swing should be impulsive
        departure_idx = min(idx + 1, len(data) - 1)
        departure_range = float(data.iloc[departure_idx]["high"] - data.iloc[departure_idx]["low"])
        if atr_val > 0 and departure_range < departure_atr_mult * atr_val:
            continue

        # Count base candles (small candles at the zone)
        base_count = 0
        for j in range(max(0, idx - max_base_candles), idx):
            rng = float(data.iloc[j]["high"] - data.iloc[j]["low"])
            if atr_val > 0 and rng < atr_val:
                base_count += 1
        if base_count > max_base_candles:
            continue

        # Determine zone boundaries
        if level.swing.swing_type == "low":
            zone_low = level.swing.price
            zone_high = float(data.iloc[idx]["high"])
            direction = "demand"
        else:
            zone_high = level.swing.price
            zone_low = float(data.iloc[idx]["low"])
            direction = "supply"

        # Check for embedded FVG
        embedded = None
        for fvg in fvgs:
            if fvg.candle_index >= idx - 2 and fvg.candle_index <= idx + 2:
                if zone_low <= fvg.low and fvg.high <= zone_high:
                    embedded = fvg
                    break

        pois.append(POI(
            zone_high=zone_high,
            zone_low=zone_low,
            timeframe=timeframe,
            direction=direction,
            created_at=data.index[idx],
            anchor_level=level,
            embedded_fvg=embedded,
            fresh=True,
            base_candles=base_count,
        ))

    return pois
