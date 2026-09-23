"""Photon Agent runner: scan loop across all pairs."""
from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from config import settings
from agents.photon.structure_engine import analyze_structure
from agents.photon.bos_choch import detect_bos_choch
from agents.photon.trend_state import determine_trend, MTFTrendView
from agents.photon.poi_detector import detect_pois
from agents.photon.liquidity_map import detect_liquidity_pools, pools_in_path
from agents.photon.eof_engine import EOFEngine, ExpectationStatus
from agents.photon.mtf_alignment import check_alignment
from agents.photon.entry_engine import check_entry_sequence
from agents.photon.trade_levels import calculate_levels
from agents.photon.news_filter import is_in_blackout
from agents.photon.signal_builder import build_photon_signal, PhotonSignal
from agents.shared.market.atr import compute_atr

logger = logging.getLogger("quant_os.agents.photon.runner")

_eof_engines: dict[str, EOFEngine] = {}


def get_eof_engine(pair: str) -> EOFEngine:
    if pair not in _eof_engines:
        _eof_engines[pair] = EOFEngine()
    return _eof_engines[pair]


def scan_pair(
    pair: str,
    d1_data: pd.DataFrame,
    h4_data: pd.DataFrame,
    m15_data: pd.DataFrame,
    ltf_data: pd.DataFrame,
    ltf_tf: str = "M5",
) -> PhotonSignal | None:
    """Run the full Photon pipeline on a single pair."""
    # Structure analysis per TF
    d1_levels = analyze_structure(d1_data, fractal_n=2)
    h4_levels = analyze_structure(h4_data, fractal_n=2)
    m15_levels = analyze_structure(m15_data, fractal_n=2)
    ltf_levels = analyze_structure(ltf_data, fractal_n=2)

    # BOS/CHoCH events
    d1_trend = determine_trend([], "D1", "perspective")
    h4_events = detect_bos_choch(h4_data, h4_levels, d1_trend.state.value)
    h4_trend = determine_trend(h4_events, "H4", "narrative")
    m15_events = detect_bos_choch(m15_data, m15_levels, h4_trend.state.value)
    m15_trend = determine_trend(m15_events, "M15", "bias")
    ltf_events = detect_bos_choch(ltf_data, ltf_levels, m15_trend.state.value)
    ltf_trend = determine_trend(ltf_events, ltf_tf, "timing")

    # Determine trade direction from H4 narrative
    if h4_trend.state.value == "BULLISH":
        direction = "LONG"
    elif h4_trend.state.value == "BEARISH":
        direction = "SHORT"
    else:
        return None

    # MTF alignment check
    alignment = check_alignment(direction, d1_trend, h4_trend, m15_trend, ltf_trend, min_alignment=3)
    if alignment.score < 3:
        return None

    # POIs on H4
    h4_pois = detect_pois(h4_data, h4_levels, "H4")

    # Liquidity pools
    pools = detect_liquidity_pools(ltf_data)

    # EOF: check active expectations
    eof = get_eof_engine(pair)

    # Create new expectations from recent H4 structure
    if h4_pois and h4_levels:
        for poi in h4_pois[-3:]:
            existing = [e for e in eof.get_active(pair)
                        if e.anticipated_price_zone == (poi.zone_low, poi.zone_high)]
            if not existing:
                eof.create_expectation(pair, direction, poi, (poi.zone_low, poi.zone_high))

    # Check price arrival on existing expectations
    current_price = float(ltf_data.iloc[-1]["close"])
    now = ltf_data.index[-1]

    for exp in eof.get_active(pair):
        eof.check_price_arrival(exp.id, current_price, now)

    # Try entry on PRICE_ARRIVED expectations
    for exp in eof.get_active(pair):
        if exp.status != ExpectationStatus.PRICE_ARRIVED:
            continue

        entry = check_entry_sequence(exp, current_price, ltf_data, pools, ltf_events, now)
        if entry is None:
            continue

        # Calculate levels
        atr_series = compute_atr(ltf_data)
        atr_val = float(atr_series.iloc[-1]) if len(atr_series) > 0 and not pd.isna(atr_series.iloc[-1]) else 0.001

        sweep_extreme = exp.anticipated_price_zone[0] if direction == "LONG" else exp.anticipated_price_zone[1]
        opposing = [p for p in pools if (p.pool_type == "BSL" if direction == "LONG" else p.pool_type == "SSL")]

        levels = calculate_levels(entry, exp.anticipated_poi, sweep_extreme, opposing, None, atr_val)

        if levels.rejected:
            continue

        pip = pools_in_path(pools, levels.entry, levels.tp1)
        signal = build_photon_signal(entry, levels, alignment, pip)
        if signal:
            eof.trigger(exp.id, now)
            logger.info("%s %s Photon signal: R:R=%.1f, basis=%s, align=%d/4",
                        pair, direction, levels.rr_to_tp1, entry.entry_basis, alignment.score)
            return signal

    return None


def scan_all_pairs(get_data_fn=None) -> list[dict]:
    """Scan all configured pairs."""
    pairs = getattr(settings, "photon_pairs", settings.crt_pairs).split(",") if isinstance(getattr(settings, "photon_pairs", settings.crt_pairs), str) else settings.crt_pairs_list

    results = []
    for pair in [p.strip() for p in pairs if p.strip()]:
        try:
            if get_data_fn is None:
                results.append({"pair": pair, "status": "no_data_fn"})
                continue

            d1 = get_data_fn(pair, "D1")
            h4 = get_data_fn(pair, "H4")
            m15 = get_data_fn(pair, "M15")
            ltf = get_data_fn(pair, "M5")

            if any(len(d) < 20 for d in [d1, h4, m15, ltf]):
                results.append({"pair": pair, "status": "insufficient_data"})
                continue

            signal = scan_pair(pair, d1, h4, m15, ltf)
            if signal:
                results.append({"pair": pair, "status": "signal", "signal": signal})
            else:
                results.append({"pair": pair, "status": "no_signal"})
        except Exception:
            logger.exception("Error scanning %s", pair)
            results.append({"pair": pair, "status": "error"})

    return results
