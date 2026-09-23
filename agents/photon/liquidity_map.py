"""Photon Module 5: Liquidity Map — BSL/SSL pools, sweep detection, pools-in-path."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from agents.shared.market.atr import compute_atr
from agents.shared.market.swings import detect_swings


@dataclass
class LiquidityPool:
    pool_type: str  # "BSL" (buy-side) or "SSL" (sell-side)
    price: float
    source: str  # "equal_highs", "equal_lows", "swing_high", "swing_low"
    timestamp: datetime
    swept: bool = False
    swept_at: datetime | None = None


def detect_liquidity_pools(
    data: pd.DataFrame,
    tolerance_atr_mult: float = 0.1,
    fractal_n: int = 2,
    lookback: int = 50,
) -> list[LiquidityPool]:
    """Detect BSL (buy-side liquidity) and SSL (sell-side liquidity) pools."""
    pools: list[LiquidityPool] = []
    recent = data.iloc[-lookback:] if len(data) > lookback else data
    atr_series = compute_atr(recent)
    atr_val = float(atr_series.iloc[-1]) if len(atr_series) > 0 and not pd.isna(atr_series.iloc[-1]) else 0
    tolerance = atr_val * tolerance_atr_mult

    highs = recent["high"].values
    lows = recent["low"].values

    # Equal highs → BSL
    for i in range(1, len(recent)):
        for j in range(i):
            if abs(float(highs[i]) - float(highs[j])) <= tolerance and tolerance > 0:
                pools.append(LiquidityPool(
                    pool_type="BSL", price=float(highs[i]),
                    source="equal_highs", timestamp=recent.index[i],
                ))
                break

    # Equal lows → SSL
    for i in range(1, len(recent)):
        for j in range(i):
            if abs(float(lows[i]) - float(lows[j])) <= tolerance and tolerance > 0:
                pools.append(LiquidityPool(
                    pool_type="SSL", price=float(lows[i]),
                    source="equal_lows", timestamp=recent.index[i],
                ))
                break

    # Swing highs → BSL, swing lows → SSL
    swings = detect_swings(recent, fractal_n)
    for s in swings:
        if s.swing_type == "high":
            pools.append(LiquidityPool("BSL", s.price, "swing_high", s.timestamp))
        else:
            pools.append(LiquidityPool("SSL", s.price, "swing_low", s.timestamp))

    return pools


def check_sweep(pool: LiquidityPool, candle_high: float, candle_low: float, candle_close: float) -> bool:
    """Check if a candle swept a liquidity pool (wick through + close back)."""
    if pool.swept:
        return False
    if pool.pool_type == "BSL" and candle_high > pool.price and candle_close < pool.price:
        return True
    if pool.pool_type == "SSL" and candle_low < pool.price and candle_close > pool.price:
        return True
    return False


def pools_in_path(pools: list[LiquidityPool], entry: float, target: float) -> list[LiquidityPool]:
    """Find unswept pools between entry and target that could stall price."""
    in_path = []
    lo, hi = min(entry, target), max(entry, target)
    for p in pools:
        if not p.swept and lo < p.price < hi:
            in_path.append(p)
    return in_path
