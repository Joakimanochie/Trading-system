"""Bias detection for backtests: look-ahead and survivorship."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


@dataclass
class BiasCheckResult:
    look_ahead_passed: bool
    survivorship_passed: bool
    truncation_sharpe_full: float
    truncation_sharpe_partial: float
    notes: list[str]


def truncation_test(
    strategy: BaseStrategy,
    data: pd.DataFrame,
    truncate_pct: float = 0.2,
) -> tuple[float, float]:
    """Run the strategy on full data vs. truncated data (last N% removed).

    If signals change on the truncated portion when future data is removed,
    the strategy has look-ahead bias.
    Returns (sharpe_full, sharpe_truncated).
    """
    import vectorbt as vbt

    signals_full = strategy.generate_signals(data)

    cutoff = int(len(data) * (1 - truncate_pct))
    data_partial = data.iloc[:cutoff]
    signals_partial = strategy.generate_signals(data_partial)

    def _sharpe(sig: pd.Series, prices: pd.Series) -> float:
        entries = sig == 1
        exits = sig == -1
        if entries.sum() == 0:
            return 0.0
        freq = prices.index.inferred_freq or "D"
        pf = vbt.Portfolio.from_signals(prices, entries=entries, exits=exits, init_cash=100_000, freq=freq)
        stats = pf.stats()
        return float(stats.get("Sharpe Ratio", 0))

    close = data["close"]
    sharpe_full = _sharpe(signals_full, close)

    close_partial = data_partial["close"]
    sharpe_partial = _sharpe(signals_partial, close_partial)

    return sharpe_full, sharpe_partial


def check_survivorship(data: pd.DataFrame, ticker: str) -> bool:
    """Basic survivorship check: verify the data doesn't start suspiciously
    late or have suspicious gaps that suggest the ticker was cherry-picked."""
    if len(data) < 252:
        logger.warning("check_survivorship(%s): less than 1 year of data", ticker)
        return False

    gaps = data.index.to_series().diff()
    max_gap = gaps.max()
    if max_gap > pd.Timedelta(days=30):
        logger.warning("check_survivorship(%s): gap of %s found", ticker, max_gap)
        return False

    return True


def run_bias_checks(
    strategy: BaseStrategy,
    data: pd.DataFrame,
    ticker: str = "UNKNOWN",
) -> BiasCheckResult:
    """Run all bias checks and return a combined result."""
    notes: list[str] = []

    sharpe_full, sharpe_partial = truncation_test(strategy, data)
    sharpe_drop = abs(sharpe_full - sharpe_partial) / max(abs(sharpe_full), 0.01)
    look_ahead_ok = sharpe_drop < 0.5  # >50% drop signals likely look-ahead bias
    if not look_ahead_ok:
        notes.append(
            f"Truncation test: Sharpe dropped {sharpe_drop:.0%} "
            f"({sharpe_full:.2f} → {sharpe_partial:.2f}) — possible look-ahead bias"
        )

    survivorship_ok = check_survivorship(data, ticker)
    if not survivorship_ok:
        notes.append(f"Survivorship check failed for {ticker}")

    return BiasCheckResult(
        look_ahead_passed=look_ahead_ok,
        survivorship_passed=survivorship_ok,
        truncation_sharpe_full=sharpe_full,
        truncation_sharpe_partial=sharpe_partial,
        notes=notes,
    )
