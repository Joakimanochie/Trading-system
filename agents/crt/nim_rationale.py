"""Generate plain-English rationale for CRT signals via OpenRouter."""
from __future__ import annotations

from agents.shared.nim_client import nim_complete
from agents.crt.signal_builder import CRTSignalData


def generate_rationale(signal: CRTSignalData) -> str:
    """Format CRT signal data as a prompt and return a plain-English rationale."""
    a = signal.anchor
    lv = signal.levels
    f = signal.filters

    prompt = (
        f"You are a CRT (Candle Range Theory) analyst. Generate a 3-4 sentence plain-English "
        f"rationale for the following signal setup:\n\n"
        f"Pair: {signal.pair}, Direction: {signal.direction}, HTF: {signal.htf}, LTF: {signal.ltf}\n"
        f"Anchor candle: High={a.crt_high:.5f}, Low={a.crt_low:.5f}, EQ={a.crt_eq:.5f}\n"
        f"Entry: {lv.entry:.5f}, SL: {lv.sl_conservative:.5f}, TP1: {lv.tp1:.5f}, TP2: {lv.tp2:.5f}\n"
        f"Filters passed: {f.passed_count}/5 (PD={f.pd_array}, Session={f.session_macro}, "
        f"Premium/Discount={f.premium_discount}, Nested={f.nested_ltf}, MSS+FVG={f.mss_fvg})\n"
        f"Kaabar confluence: {signal.confluence_score} patterns ({', '.join(signal.confluence_patterns) or 'none'})\n\n"
        f"Explain why this is a {'bullish' if signal.direction == 'LONG' else 'bearish'} setup, "
        f"referencing the sweep, MSS, and key levels."
    )

    return nim_complete(prompt, temperature=0.5, max_tokens=400, stream=True)
