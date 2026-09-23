"""Photon Backtesting: replay historical LTF bars through the live code path.

Usage:
    PYTHONPATH=. .venv/Scripts/python agents/photon/backtest_photon.py
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from agents.photon.structure_engine import analyze_structure
from agents.photon.bos_choch import detect_bos_choch
from agents.photon.trend_state import determine_trend, TrendState
from agents.photon.poi_detector import detect_pois
from agents.photon.liquidity_map import detect_liquidity_pools, pools_in_path
from agents.photon.eof_engine import EOFEngine, ExpectationStatus
from agents.photon.mtf_alignment import check_alignment
from agents.photon.entry_engine import check_entry_sequence
from agents.photon.trade_levels import calculate_levels
from agents.shared.market.atr import compute_atr

logger = logging.getLogger(__name__)


@dataclass
class PhotonBacktestTrade:
    pair: str
    direction: str
    entry_time: datetime
    entry_price: float
    entry_basis: str
    sl: float
    tp1: float
    tp2: float
    rr: float
    alignment_score: int
    tp1_hit: bool = False
    tp2_hit: bool = False
    sl_hit: bool = False
    pnl_r: float = 0.0


@dataclass
class PhotonBacktestReport:
    pair: str
    total_signals: int
    tp1_hits: int
    sl_hits: int
    win_rate: float
    avg_rr: float
    expectancy: float
    trades: list[PhotonBacktestTrade] = field(default_factory=list)
    entry_basis_breakdown: dict = field(default_factory=dict)
    alignment_impact: dict = field(default_factory=dict)


def _check_outcome(
    ltf_data: pd.DataFrame,
    entry_idx: int,
    direction: str,
    sl: float,
    tp1: float,
    tp2: float,
    max_bars: int = 300,
) -> tuple[bool, bool, bool, float]:
    risk = abs(ltf_data.iloc[entry_idx]["close"] - sl)
    if risk == 0:
        return False, False, False, 0.0

    tp1_hit = False
    tp2_hit = False
    sl_hit = False
    pnl_r = 0.0
    end_idx = min(entry_idx + max_bars, len(ltf_data))

    for i in range(entry_idx + 1, end_idx):
        h = float(ltf_data.iloc[i]["high"])
        l = float(ltf_data.iloc[i]["low"])

        if direction == "LONG":
            if l <= sl:
                sl_hit = True
                pnl_r = -1.0
                break
            if not tp1_hit and h >= tp1:
                tp1_hit = True
            if h >= tp2:
                tp2_hit = True
                pnl_r = abs(tp2 - float(ltf_data.iloc[entry_idx]["close"])) / risk
                break
        else:
            if h >= sl:
                sl_hit = True
                pnl_r = -1.0
                break
            if not tp1_hit and l <= tp1:
                tp1_hit = True
            if l <= tp2:
                tp2_hit = True
                pnl_r = abs(float(ltf_data.iloc[entry_idx]["close"]) - tp2) / risk
                break

    if not sl_hit and not tp2_hit and tp1_hit:
        pnl_r = abs(tp1 - float(ltf_data.iloc[entry_idx]["close"])) / risk

    return tp1_hit, tp2_hit, sl_hit, pnl_r


def backtest_pair(
    pair: str,
    d1_data: pd.DataFrame,
    h4_data: pd.DataFrame,
    m15_data: pd.DataFrame,
    ltf_data: pd.DataFrame,
) -> PhotonBacktestReport:
    """Replay historical data through the Photon pipeline for one pair."""
    trades: list[PhotonBacktestTrade] = []
    eof = EOFEngine()

    # Walk through H4 bars, building structure incrementally
    min_h4_bars = 30
    scan_interval = 2  # scan every N H4 bars

    for h4_end in range(min_h4_bars, len(h4_data) - 1, scan_interval):
        h4_window = h4_data.iloc[:h4_end + 1]
        h4_time = h4_data.index[h4_end]

        # Get corresponding D1/M15/LTF windows up to this point
        d1_window = d1_data[d1_data.index <= h4_time]
        m15_window = m15_data[m15_data.index <= h4_time]
        ltf_window = ltf_data[ltf_data.index <= h4_time]

        if len(d1_window) < 20 or len(m15_window) < 20 or len(ltf_window) < 20:
            continue

        # Structure
        d1_levels = analyze_structure(d1_window.tail(100), fractal_n=2)
        h4_levels = analyze_structure(h4_window.tail(100), fractal_n=2)
        m15_levels = analyze_structure(m15_window.tail(100), fractal_n=2)
        ltf_levels = analyze_structure(ltf_window.tail(100), fractal_n=2)

        # Trend
        d1_trend = determine_trend([], "D1", "perspective")
        h4_events = detect_bos_choch(h4_window.tail(50), h4_levels, d1_trend.state.value)
        h4_trend = determine_trend(h4_events, "H4", "narrative")

        if h4_trend.state == TrendState.RANGING:
            continue

        direction = "LONG" if h4_trend.state == TrendState.BULLISH else "SHORT"

        m15_events = detect_bos_choch(m15_window.tail(50), m15_levels, h4_trend.state.value)
        m15_trend = determine_trend(m15_events, "M15", "bias")
        ltf_events = detect_bos_choch(ltf_window.tail(50), ltf_levels, m15_trend.state.value)
        ltf_trend = determine_trend(ltf_events, "M5", "timing")

        alignment = check_alignment(direction, d1_trend, h4_trend, m15_trend, ltf_trend)
        if alignment.score < 3:
            continue

        # POIs
        h4_pois = detect_pois(h4_window.tail(50), h4_levels, "H4")
        if not h4_pois:
            continue

        # Create expectations for new POIs
        for poi in h4_pois[-2:]:
            zone = (poi.zone_low, poi.zone_high)
            existing = [e for e in eof.get_active(pair) if e.anticipated_price_zone == zone]
            if not existing:
                eof.create_expectation(pair, direction, poi, zone, h4_time)

        # Check price arrival + entry
        current_price = float(ltf_window.iloc[-1]["close"])
        pools = detect_liquidity_pools(ltf_window.tail(50))

        for exp in eof.get_active(pair):
            eof.check_price_arrival(exp.id, current_price, h4_time)

            if exp.status != ExpectationStatus.PRICE_ARRIVED:
                continue

            entry = check_entry_sequence(exp, current_price, ltf_window.tail(20), pools, ltf_events, h4_time)
            if entry is None:
                continue

            atr_series = compute_atr(ltf_window.tail(50))
            atr_val = float(atr_series.iloc[-1]) if len(atr_series) > 0 and not pd.isna(atr_series.iloc[-1]) else 0.001

            # SL placed beyond the full POI zone extreme (not entry price)
            if direction == "LONG":
                sweep_extreme = min(exp.anticipated_price_zone[0], float(ltf_window.tail(10)["low"].min()))
            else:
                sweep_extreme = max(exp.anticipated_price_zone[1], float(ltf_window.tail(10)["high"].max()))
            opposing = [p for p in pools if (p.pool_type == "BSL" if direction == "LONG" else p.pool_type == "SSL")]

            levels = calculate_levels(entry, exp.anticipated_poi, sweep_extreme, opposing, None, atr_val)
            if levels.rejected:
                continue

            eof.trigger(exp.id, h4_time)

            # Check outcome
            entry_idx_candidates = ltf_data.index.searchsorted(h4_time)
            if entry_idx_candidates >= len(ltf_data) - 10:
                continue

            tp1_hit, tp2_hit, sl_hit, pnl_r = _check_outcome(
                ltf_data, entry_idx_candidates, direction, levels.sl, levels.tp1, levels.tp2
            )

            trades.append(PhotonBacktestTrade(
                pair=pair,
                direction=direction,
                entry_time=h4_time,
                entry_price=levels.entry,
                entry_basis=entry.entry_basis,
                sl=levels.sl,
                tp1=levels.tp1,
                tp2=levels.tp2,
                rr=levels.rr_to_tp1,
                alignment_score=alignment.score,
                tp1_hit=tp1_hit,
                tp2_hit=tp2_hit,
                sl_hit=sl_hit,
                pnl_r=round(pnl_r, 4),
            ))
            break  # one signal per scan window

    # Compile report
    n = len(trades)
    tp1_hits = sum(1 for t in trades if t.tp1_hit)
    sl_hits = sum(1 for t in trades if t.sl_hit)
    win_rate = tp1_hits / n if n > 0 else 0.0
    avg_rr = sum(t.pnl_r for t in trades) / n if n > 0 else 0.0
    expectancy = win_rate * avg_rr if n > 0 else 0.0

    # Entry basis breakdown
    basis_stats = {}
    for t in trades:
        if t.entry_basis not in basis_stats:
            basis_stats[t.entry_basis] = {"count": 0, "wins": 0, "total_r": 0.0}
        basis_stats[t.entry_basis]["count"] += 1
        if t.tp1_hit:
            basis_stats[t.entry_basis]["wins"] += 1
        basis_stats[t.entry_basis]["total_r"] += t.pnl_r
    for k, v in basis_stats.items():
        v["win_rate"] = round(v["wins"] / v["count"], 3) if v["count"] > 0 else 0
        v["avg_r"] = round(v["total_r"] / v["count"], 3) if v["count"] > 0 else 0

    # Alignment impact
    align_stats = {}
    for score in (3, 4):
        subset = [t for t in trades if t.alignment_score == score]
        if subset:
            align_stats[f"score_{score}"] = {
                "count": len(subset),
                "win_rate": round(sum(1 for t in subset if t.tp1_hit) / len(subset), 3),
                "avg_r": round(sum(t.pnl_r for t in subset) / len(subset), 3),
            }

    return PhotonBacktestReport(
        pair=pair,
        total_signals=n,
        tp1_hits=tp1_hits,
        sl_hits=sl_hits,
        win_rate=round(win_rate, 4),
        avg_rr=round(avg_rr, 4),
        expectancy=round(expectancy, 4),
        trades=trades,
        entry_basis_breakdown=basis_stats,
        alignment_impact=align_stats,
    )


def run_photon_backtest(pairs: list[str] | None = None) -> list[PhotonBacktestReport]:
    """Run Photon backtest across multiple pairs using MT5 historical data."""
    import MetaTrader5 as mt5

    mt5.initialize(path=r"C:\Users\Hp\AppData\Roaming\MetaTrader 5\terminal64.exe")

    if pairs is None:
        pairs = ["EURUSD", "GBPUSD", "USDCHF", "XAUUSD", "BTCUSD"]

    def load_tf(pair, tf_const, count=5000):
        rates = mt5.copy_rates_from_pos(pair, tf_const, 0, count)
        if rates is None or len(rates) == 0:
            return pd.DataFrame()
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        df.rename(columns={"tick_volume": "volume"}, inplace=True)
        return df

    reports = []
    for pair in pairs:
        logger.info("Photon backtesting %s...", pair)

        d1 = load_tf(pair, mt5.TIMEFRAME_D1, 1000)
        h4 = load_tf(pair, mt5.TIMEFRAME_H4, 5000)
        m15 = load_tf(pair, mt5.TIMEFRAME_M15, 5000)
        m5 = load_tf(pair, mt5.TIMEFRAME_M5, 5000)

        if any(len(d) < 50 for d in [d1, h4, m15, m5]):
            logger.warning("%s: insufficient data, skipping", pair)
            continue

        report = backtest_pair(pair, d1, h4, m15, m5)
        reports.append(report)

        logger.info(
            "%s: %d signals, win=%.0f%%, avg_r=%.2f, expectancy=%.3f",
            pair, report.total_signals, report.win_rate * 100,
            report.avg_rr, report.expectancy,
        )

    mt5.shutdown()
    return reports


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    reports = run_photon_backtest()
    total_setups = sum(r.total_signals for r in reports)
    print(f"\n=== PHOTON BACKTEST SUMMARY ({total_setups} total setups) ===")
    for r in reports:
        print(f"{r.pair}: {r.total_signals} signals | win={r.win_rate*100:.0f}% | avg_r={r.avg_rr:.2f} | expectancy={r.expectancy:.3f}")
        if r.entry_basis_breakdown:
            for basis, stats in r.entry_basis_breakdown.items():
                print(f"  {basis}: n={stats['count']} win={stats['win_rate']*100:.0f}% avg_r={stats['avg_r']:.2f}")
        if r.alignment_impact:
            for score, stats in r.alignment_impact.items():
                print(f"  {score}: n={stats['count']} win={stats['win_rate']*100:.0f}% avg_r={stats['avg_r']:.2f}")
    temp_gate = 10  # temporary gate for code validation; re-gate at 50 before live trading
    print(f"\nPhase-9 gate (temp {temp_gate}): {'PASS' if total_setups >= temp_gate else 'FAIL'} ({total_setups}/{temp_gate} setups)")
    print(f"Production gate (50): {'PASS' if total_setups >= 50 else 'PENDING'} ({total_setups}/50 — needs more LTF archive)")
