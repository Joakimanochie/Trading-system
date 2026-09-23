"""CRT Backtesting: replay historical HTF + LTF data and evaluate CRT signal performance.

Usage:
    PYTHONPATH=. .venv/Scripts/python agents/crt/backtest_crt.py
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

from agents.crt.anchor import identify_anchor, AnchorCandle
from agents.crt.sweep_detector import detect_sweep, SweepType
from agents.crt.levels import calculate_levels, CRTLevels
from agents.crt.signal_builder import compute_confluence

logger = logging.getLogger(__name__)


@dataclass
class CRTBacktestTrade:
    pair: str
    direction: str
    entry_time: datetime
    entry_price: float
    sl: float
    tp1: float
    tp2: float
    tp1_hit: bool = False
    tp2_hit: bool = False
    sl_hit: bool = False
    pnl_r: float = 0.0
    confluence_patterns: list[str] = field(default_factory=list)
    confluence_score: int = 0


@dataclass
class CRTBacktestReport:
    pair: str
    total_signals: int
    tp1_hits: int
    tp2_hits: int
    sl_hits: int
    hit_ratio_tp1: float
    profit_factor: float
    avg_rr: float
    signal_frequency_per_month: float
    trades: list[CRTBacktestTrade] = field(default_factory=list)
    confluence_impact: dict = field(default_factory=dict)


def _check_outcome(
    ltf_data: pd.DataFrame,
    entry_idx: int,
    direction: str,
    levels: CRTLevels,
    max_bars: int = 200,
) -> tuple[bool, bool, bool, float]:
    """Walk forward from entry_idx on LTF to see if TP1/TP2/SL is hit first."""
    tp1_hit = False
    tp2_hit = False
    sl_hit = False
    pnl_r = 0.0

    risk = abs(levels.entry - levels.sl_conservative)
    if risk == 0:
        return False, False, False, 0.0

    end_idx = min(entry_idx + max_bars, len(ltf_data))

    for i in range(entry_idx + 1, end_idx):
        h = float(ltf_data.iloc[i]["high"])
        l = float(ltf_data.iloc[i]["low"])

        if direction == "LONG":
            if l <= levels.sl_conservative:
                sl_hit = True
                pnl_r = -1.0
                break
            if not tp1_hit and h >= levels.tp1:
                tp1_hit = True
            if h >= levels.tp2:
                tp2_hit = True
                pnl_r = abs(levels.tp2 - levels.entry) / risk
                break
        else:
            if h >= levels.sl_conservative:
                sl_hit = True
                pnl_r = -1.0
                break
            if not tp1_hit and l <= levels.tp1:
                tp1_hit = True
            if l <= levels.tp2:
                tp2_hit = True
                pnl_r = abs(levels.entry - levels.tp2) / risk
                break

    if not sl_hit and not tp2_hit and tp1_hit:
        pnl_r = abs(levels.tp1 - levels.entry) / risk

    return tp1_hit, tp2_hit, sl_hit, pnl_r


def backtest_pair(
    pair: str,
    htf_data: pd.DataFrame,
    ltf_data: pd.DataFrame,
    htf: str = "H4",
    ltf: str = "M5",
) -> CRTBacktestReport:
    """Replay historical data for a single pair and collect CRT trade outcomes."""
    trades: list[CRTBacktestTrade] = []

    for anchor_end in range(3, len(htf_data) - 2):
        htf_window = htf_data.iloc[: anchor_end + 2]
        anchor = identify_anchor(htf_window, pair, htf)
        if anchor is None:
            continue

        sweep = detect_sweep(htf_window, anchor)
        if sweep.sweep_type not in (SweepType.SWEEP_LOW, SweepType.SWEEP_HIGH):
            continue

        direction = sweep.direction
        levels = calculate_levels(anchor, direction)

        sweep_time = htf_data.index[sweep.sweep_candle_idx]
        ltf_after = ltf_data[ltf_data.index >= sweep_time]
        if len(ltf_after) < 10:
            continue

        entry_idx = ltf_data.index.get_loc(ltf_after.index[0])
        if isinstance(entry_idx, slice):
            entry_idx = entry_idx.start

        patterns, score = compute_confluence(ltf_after.head(20), direction)

        tp1_hit, tp2_hit, sl_hit, pnl_r = _check_outcome(
            ltf_data, entry_idx, direction, levels
        )

        trades.append(CRTBacktestTrade(
            pair=pair,
            direction=direction,
            entry_time=ltf_data.index[entry_idx],
            entry_price=levels.entry,
            sl=levels.sl_conservative,
            tp1=levels.tp1,
            tp2=levels.tp2,
            tp1_hit=tp1_hit,
            tp2_hit=tp2_hit,
            sl_hit=sl_hit,
            pnl_r=round(pnl_r, 4),
            confluence_patterns=patterns,
            confluence_score=score,
        ))

    n = len(trades)
    tp1_hits = sum(1 for t in trades if t.tp1_hit)
    tp2_hits = sum(1 for t in trades if t.tp2_hit)
    sl_hits = sum(1 for t in trades if t.sl_hit)
    hit_ratio = tp1_hits / n if n > 0 else 0.0

    gross_profit = sum(t.pnl_r for t in trades if t.pnl_r > 0)
    gross_loss = abs(sum(t.pnl_r for t in trades if t.pnl_r < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0

    avg_rr = (sum(t.pnl_r for t in trades) / n) if n > 0 else 0.0

    if len(htf_data) > 1:
        span_days = (htf_data.index[-1] - htf_data.index[0]).days
        months = max(span_days / 30, 1)
        freq = n / months
    else:
        freq = 0.0

    # Confluence impact: hit ratio with vs without each pattern
    confluence_impact = {}
    all_pattern_names = set()
    for t in trades:
        all_pattern_names.update(t.confluence_patterns)
    for pat in all_pattern_names:
        with_pat = [t for t in trades if pat in t.confluence_patterns]
        without_pat = [t for t in trades if pat not in t.confluence_patterns]
        hr_with = sum(1 for t in with_pat if t.tp1_hit) / len(with_pat) if with_pat else 0
        hr_without = sum(1 for t in without_pat if t.tp1_hit) / len(without_pat) if without_pat else 0
        confluence_impact[pat] = {"with": round(hr_with, 3), "without": round(hr_without, 3), "count": len(with_pat)}

    return CRTBacktestReport(
        pair=pair,
        total_signals=n,
        tp1_hits=tp1_hits,
        tp2_hits=tp2_hits,
        sl_hits=sl_hits,
        hit_ratio_tp1=round(hit_ratio, 4),
        profit_factor=round(profit_factor, 4),
        avg_rr=round(avg_rr, 4),
        signal_frequency_per_month=round(freq, 2),
        trades=trades,
        confluence_impact=confluence_impact,
    )


def run_crt_backtest(pairs: list[str] | None = None) -> list[CRTBacktestReport]:
    """Run CRT backtest across multiple pairs using MT5 historical data."""
    import MetaTrader5 as mt5

    mt5.initialize(path=r"C:\Users\Hp\AppData\Roaming\MetaTrader 5\terminal64.exe")

    if pairs is None:
        pairs = ["EURUSD", "GBPUSD", "USDCHF", "XAUUSD", "BTCUSD"]

    reports = []
    for pair in pairs:
        logger.info("Backtesting %s...", pair)
        h4 = mt5.copy_rates_from_pos(pair, mt5.TIMEFRAME_H4, 0, 5000)
        m5 = mt5.copy_rates_from_pos(pair, mt5.TIMEFRAME_M5, 0, 5000)

        if h4 is None or m5 is None or len(h4) < 100 or len(m5) < 100:
            logger.warning("%s: insufficient data, skipping", pair)
            continue

        htf_df = pd.DataFrame(h4)
        htf_df["time"] = pd.to_datetime(htf_df["time"], unit="s")
        htf_df.set_index("time", inplace=True)

        ltf_df = pd.DataFrame(m5)
        ltf_df["time"] = pd.to_datetime(ltf_df["time"], unit="s")
        ltf_df.set_index("time", inplace=True)

        report = backtest_pair(pair, htf_df, ltf_df)
        reports.append(report)

        logger.info(
            "%s: %d signals, TP1 hit=%d (%.0f%%), PF=%.2f, avg R:R=%.2f, freq=%.1f/mo",
            pair, report.total_signals, report.tp1_hits,
            report.hit_ratio_tp1 * 100, report.profit_factor,
            report.avg_rr, report.signal_frequency_per_month,
        )

    mt5.shutdown()
    return reports


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    reports = run_crt_backtest()
    print("\n=== CRT BACKTEST SUMMARY ===")
    for r in reports:
        print(f"{r.pair}: {r.total_signals} signals | TP1 hit: {r.hit_ratio_tp1*100:.0f}% | PF: {r.profit_factor} | avg R:R: {r.avg_rr} | {r.signal_frequency_per_month}/mo")
        if r.confluence_impact:
            print(f"  Confluence impact:")
            for pat, info in sorted(r.confluence_impact.items(), key=lambda x: x[1]["with"], reverse=True):
                print(f"    {pat}: hit rate with={info['with']*100:.0f}% without={info['without']*100:.0f}% (n={info['count']})")
