"""Photon Module 9: Trade Levels — SL, TP1, TP2 with hard min-R:R gate."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from agents.photon.entry_engine import EntrySignal
from agents.photon.liquidity_map import LiquidityPool
from agents.photon.poi_detector import POI

logger = logging.getLogger(__name__)


@dataclass
class PhotonTradeLevels:
    entry: float
    sl: float
    tp1: float
    tp2: float
    rr_to_tp1: float
    rejected: bool = False
    reject_reason: str = ""


def calculate_levels(
    entry_signal: EntrySignal,
    poi: POI | None,
    sweep_extreme: float,
    opposing_pools: list[LiquidityPool],
    next_poi_price: float | None,
    atr_value: float,
    sl_buffer_mult: float = 0.3,
    min_rr: float = 2.0,
) -> PhotonTradeLevels:
    """Calculate SL/TP with hard min-R:R gate.

    SL: beyond POI/sweep extreme + ATR buffer.
    TP1: nearest opposing liquidity pool (partial + move SL to BE).
    TP2: next POI or structural target.
    """
    buffer = atr_value * sl_buffer_mult

    if entry_signal.direction == "LONG":
        sl = sweep_extreme - buffer
        # TP1 = nearest BSL pool above entry
        tp1 = None
        for p in sorted(opposing_pools, key=lambda x: x.price):
            if p.pool_type == "BSL" and p.price > entry_signal.entry_price and not p.swept:
                tp1 = p.price
                break
        if tp1 is None:
            tp1 = entry_signal.entry_price + (entry_signal.entry_price - sl) * min_rr
        tp2 = next_poi_price or tp1 * 1.5
    else:
        sl = sweep_extreme + buffer
        tp1 = None
        for p in sorted(opposing_pools, key=lambda x: x.price, reverse=True):
            if p.pool_type == "SSL" and p.price < entry_signal.entry_price and not p.swept:
                tp1 = p.price
                break
        if tp1 is None:
            tp1 = entry_signal.entry_price - (sl - entry_signal.entry_price) * min_rr
        tp2 = next_poi_price or tp1 * 0.5

    risk = abs(entry_signal.entry_price - sl)
    reward = abs(tp1 - entry_signal.entry_price)
    rr = reward / risk if risk > 0 else 0.0

    rejected = rr < min_rr
    reason = ""
    if rejected:
        reason = f"R:R {rr:.2f} below minimum {min_rr}"
        logger.warning("Signal REJECTED: %s %s — %s", entry_signal.pair, entry_signal.direction, reason)

    return PhotonTradeLevels(
        entry=round(entry_signal.entry_price, 6),
        sl=round(sl, 6),
        tp1=round(tp1, 6),
        tp2=round(tp2, 6),
        rr_to_tp1=round(rr, 2),
        rejected=rejected,
        reject_reason=reason,
    )
