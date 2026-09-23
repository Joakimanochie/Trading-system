"""Photon Module 8: Entry Engine — the mechanical sequence.

ALL three hard requirements must be met in sequence:
1. Price inside a PRICE_ARRIVED expectation's POI
2. Liquidity sweep confirmed at/around the zone
3. LTF BOS in trade direction
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from agents.photon.eof_engine import Expectation, ExpectationStatus
from agents.photon.liquidity_map import LiquidityPool, check_sweep
from agents.photon.bos_choch import StructureEvent, EventType
from agents.shared.market.fvg import FVG


@dataclass
class EntrySignal:
    expectation_id: str
    pair: str
    direction: str
    entry_price: float
    entry_basis: str  # "fvg_in_poi", "bos_close", "zone_limit"
    sweep_confirmed: bool
    ltf_bos_confirmed: bool
    timestamp: datetime


def check_entry_sequence(
    expectation: Expectation,
    current_price: float,
    ltf_data: pd.DataFrame,
    pools: list[LiquidityPool],
    ltf_events: list[StructureEvent],
    timestamp: datetime,
) -> EntrySignal | None:
    """Run the mechanical entry sequence. Returns a signal only if all 3 conditions pass."""
    if expectation.status != ExpectationStatus.PRICE_ARRIVED:
        return None

    # Condition 1: price inside the POI zone
    lo, hi = expectation.anticipated_price_zone
    if not (lo <= current_price <= hi):
        return None

    # Condition 2: liquidity sweep confirmed
    sweep_confirmed = False
    if len(ltf_data) > 0:
        last = ltf_data.iloc[-1]
        for pool in pools:
            if check_sweep(pool, float(last["high"]), float(last["low"]), float(last["close"])):
                pool.swept = True
                pool.swept_at = timestamp
                sweep_confirmed = True
                break

    if not sweep_confirmed:
        return None

    # Condition 3: LTF BOS in trade direction
    ltf_bos = False
    for event in reversed(ltf_events):
        if event.event_type == EventType.BOS:
            if expectation.direction == "LONG" and event.level_broken.swing.swing_type == "high":
                ltf_bos = True
            elif expectation.direction == "SHORT" and event.level_broken.swing.swing_type == "low":
                ltf_bos = True
            break

    if not ltf_bos:
        return None

    # Determine entry price and basis
    entry_price = current_price
    entry_basis = "bos_close"

    if expectation.anticipated_poi and expectation.anticipated_poi.embedded_fvg:
        fvg = expectation.anticipated_poi.embedded_fvg
        entry_price = (fvg.high + fvg.low) / 2
        entry_basis = "fvg_in_poi"

    return EntrySignal(
        expectation_id=expectation.id,
        pair=expectation.pair,
        direction=expectation.direction,
        entry_price=entry_price,
        entry_basis=entry_basis,
        sweep_confirmed=True,
        ltf_bos_confirmed=True,
        timestamp=timestamp,
    )
