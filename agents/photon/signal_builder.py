"""Photon signal assembly: combine all modules into a PhotonSignal."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from agents.photon.entry_engine import EntrySignal
from agents.photon.trade_levels import PhotonTradeLevels
from agents.photon.mtf_alignment import AlignmentResult
from agents.photon.liquidity_map import LiquidityPool


@dataclass
class PhotonSignal:
    pair: str
    direction: str
    expectation_id: str
    entry_basis: str
    levels: PhotonTradeLevels
    alignment: AlignmentResult
    liquidity_context: dict = field(default_factory=dict)
    rr: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


def build_photon_signal(
    entry: EntrySignal,
    levels: PhotonTradeLevels,
    alignment: AlignmentResult,
    pools_in_path: list[LiquidityPool] | None = None,
) -> PhotonSignal | None:
    """Assemble a PhotonSignal. Returns None if levels were rejected."""
    if levels.rejected:
        return None

    return PhotonSignal(
        pair=entry.pair,
        direction=entry.direction,
        expectation_id=entry.expectation_id,
        entry_basis=entry.entry_basis,
        levels=levels,
        alignment=alignment,
        liquidity_context={
            "pools_in_path": len(pools_in_path) if pools_in_path else 0,
            "sweep_confirmed": entry.sweep_confirmed,
        },
        rr=levels.rr_to_tp1,
    )
