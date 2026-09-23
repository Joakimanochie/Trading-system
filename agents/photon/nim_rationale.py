"""Photon signal rationale via OpenRouter."""
from __future__ import annotations

from agents.shared.nim_client import nim_complete
from agents.photon.signal_builder import PhotonSignal


def generate_rationale(signal: PhotonSignal) -> str:
    lv = signal.levels
    al = signal.alignment

    prompt = (
        f"You are a Photon/SMC analyst. Generate a 3-4 sentence plain-English "
        f"rationale for this Expectational Orderflow signal:\n\n"
        f"Pair: {signal.pair}, Direction: {signal.direction}\n"
        f"Entry: {lv.entry:.5f} ({signal.entry_basis}), SL: {lv.sl:.5f}, "
        f"TP1: {lv.tp1:.5f}, TP2: {lv.tp2:.5f}, R:R: {lv.rr_to_tp1:.1f}\n"
        f"MTF Alignment: {al.score}/4 (D1={al.d1_aligned}, H4={al.h4_aligned}, "
        f"M15={al.m15_aligned}, LTF={al.ltf_aligned})\n"
        f"Expectation ID: {signal.expectation_id}\n"
        f"Liquidity: {signal.liquidity_context}\n\n"
        f"Explain the setup referencing the expectation, POI arrival, sweep, and LTF BOS."
    )

    return nim_complete(prompt, temperature=0.5, max_tokens=400, stream=True)
