"""CRT Agent main loop: scan all pairs, run full pipeline, emit signals."""
from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from config import settings
from agents.crt.anchor import identify_anchor
from agents.crt.sweep_detector import detect_sweep, SweepType
from agents.crt.nested_crt import detect_nested_crt
from agents.crt.mss_detector import detect_mss
from agents.crt.levels import calculate_levels
from agents.crt.filters import evaluate_filters
from agents.crt.session_clock import is_in_session
from agents.crt.signal_builder import build_signal, CRTSignalData

logger = logging.getLogger("quant_os.agents.crt.runner")


def scan_pair(
    pair: str,
    htf_data: pd.DataFrame,
    ltf_data: pd.DataFrame,
    htf: str = "H4",
    ltf: str = "M5",
) -> CRTSignalData | None:
    """Run the full CRT pipeline on a single pair. Returns a signal or None."""
    anchor = identify_anchor(htf_data, pair, htf)
    if anchor is None:
        logger.debug("%s: not enough HTF data for anchor", pair)
        return None

    sweep = detect_sweep(htf_data, anchor)
    if sweep.sweep_type not in (SweepType.SWEEP_LOW, SweepType.SWEEP_HIGH):
        logger.debug("%s: no sweep detected (%s)", pair, sweep.sweep_type)
        return None

    direction = sweep.direction

    nested = detect_nested_crt(
        ltf_data,
        sweep_zone_high=anchor.crt_high,
        sweep_zone_low=anchor.crt_low,
        direction=direction,
    )

    mss = detect_mss(ltf_data, direction)

    levels = calculate_levels(anchor, direction)

    in_session = is_in_session()
    filters = evaluate_filters(anchor, direction, levels.entry, nested, mss, in_session)

    signal = build_signal(pair, direction, htf, ltf, anchor, levels, filters, mss, ltf_data)

    logger.info(
        "%s %s signal: filters=%d/5, confluence=%d, entry=%.5f, SL=%.5f, TP1=%.5f",
        pair, direction, filters.passed_count, signal.confluence_score,
        levels.entry, levels.sl_conservative, levels.tp1,
    )

    return signal


def scan_all_pairs(
    get_data_fn=None,
) -> list[dict]:
    """Iterate all CRT_PAIRS and run the full CRT pipeline for each.

    `get_data_fn(pair, timeframe)` should return a pd.DataFrame with OHLC columns.
    If not provided, pulls from MT5 via the connector.
    """
    if get_data_fn is None:
        from data.mt5.connector import get_quotes
        import MetaTrader5 as mt5

        def get_data_fn(pair: str, timeframe_str: str) -> pd.DataFrame:
            tf_map = {"H4": mt5.TIMEFRAME_H4, "M5": mt5.TIMEFRAME_M5}
            tf = tf_map.get(timeframe_str)
            if tf is None:
                return pd.DataFrame()
            rates = mt5.copy_rates_from_pos(pair, tf, 0, 200)
            if rates is None or len(rates) == 0:
                return pd.DataFrame()
            df = pd.DataFrame(rates)
            df["time"] = pd.to_datetime(df["time"], unit="s")
            df.set_index("time", inplace=True)
            df.rename(columns={"tick_volume": "volume"}, inplace=True)
            return df

    htf = settings.crt_htf
    ltf = settings.crt_ltf
    results = []

    for pair in settings.crt_pairs_list:
        try:
            htf_data = get_data_fn(pair, htf)
            ltf_data = get_data_fn(pair, ltf)

            if len(htf_data) < 5 or len(ltf_data) < 20:
                results.append({"pair": pair, "status": "insufficient_data"})
                continue

            signal = scan_pair(pair, htf_data, ltf_data, htf, ltf)

            if signal is None:
                results.append({"pair": pair, "status": "no_signal"})
            else:
                results.append({
                    "pair": pair,
                    "status": "signal",
                    "direction": signal.direction,
                    "filters": signal.filters.passed_count,
                    "confluence": signal.confluence_score,
                    "entry": signal.levels.entry,
                    "sl": signal.levels.sl_conservative,
                    "tp1": signal.levels.tp1,
                    "tp2": signal.levels.tp2,
                    "signal": signal,
                })

        except Exception:
            logger.exception("Error scanning %s", pair)
            results.append({"pair": pair, "status": "error"})

    return results
