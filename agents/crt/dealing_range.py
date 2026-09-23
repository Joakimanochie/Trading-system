"""Higher-TF dealing range for premium/discount filter.

Premium/discount is measured against a D1 dealing range (major swing high ↔ low),
NOT against the anchor candle itself (which would be circular).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DealingRange:
    swing_high: float
    swing_low: float
    eq_50: float
    premium_zone_start: float  # above EQ
    discount_zone_end: float   # below EQ


def find_dealing_range(
    higher_tf_data: pd.DataFrame,
    lookback: int = 20,
) -> DealingRange | None:
    """Find the most recent major swing high and swing low on the higher TF."""
    if len(higher_tf_data) < lookback:
        return None

    recent = higher_tf_data.iloc[-lookback:]
    swing_high = float(recent["high"].max())
    swing_low = float(recent["low"].min())
    eq = swing_low + (swing_high - swing_low) * 0.5

    return DealingRange(
        swing_high=swing_high,
        swing_low=swing_low,
        eq_50=eq,
        premium_zone_start=eq,
        discount_zone_end=eq,
    )


def is_in_discount(price: float, dealing_range: DealingRange) -> bool:
    """Returns True if price is below the dealing range's 50% EQ (discount zone)."""
    return price < dealing_range.eq_50


def is_in_premium(price: float, dealing_range: DealingRange) -> bool:
    """Returns True if price is above the dealing range's 50% EQ (premium zone)."""
    return price > dealing_range.eq_50


def validate_premium_discount(
    direction: str,
    sweep_price: float,
    dealing_range: DealingRange,
) -> bool:
    """Validate: bullish CRT only in discount, bearish only in premium.

    Measured against the higher-TF dealing range, not the anchor candle.
    """
    if direction == "LONG":
        return is_in_discount(sweep_price, dealing_range)
    else:
        return is_in_premium(sweep_price, dealing_range)
