"""Backtesting runner: strategy config → VectorBT backtest → BacktestReport."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd
import vectorbt as vbt

from agents.backtesting.bias_checks import run_bias_checks, BiasCheckResult
from agents.backtesting.cost_model import CostModel
from agents.backtesting.monte_carlo import permutation_test, MonteCarloResult
from agents.backtesting.report import build_report, BacktestReport
from agents.backtesting.sensitivity import (
    sensitivity_analysis,
    detect_overfitting,
    SensitivityResult,
)
from agents.backtesting.walk_forward import walk_forward, WalkForwardResult
from strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


@dataclass
class FullBacktestResult:
    report: BacktestReport
    bias_checks: BiasCheckResult
    walk_forward: WalkForwardResult
    monte_carlo: MonteCarloResult
    sensitivity: list[SensitivityResult]
    overfitting_flags: list[str]
    cost_model: CostModel


def run_backtest(
    strategy: BaseStrategy,
    data: pd.DataFrame,
    ticker: str = "UNKNOWN",
    cost_model: CostModel | None = None,
    parameters: dict[str, float] | None = None,
    mc_simulations: int = 500,
    wf_windows: int = 5,
) -> FullBacktestResult:
    """Run the full backtesting pipeline on a strategy + data pair.

    Returns a FullBacktestResult containing the performance report,
    bias checks, walk-forward analysis, Monte Carlo test, sensitivity
    analysis, and overfitting detection.
    """
    if cost_model is None:
        cost_model = CostModel()

    close = data["close"]
    signals = strategy.generate_signals(data)
    entries = signals == 1
    exits = signals == -1

    fees = cost_model.total_pct

    if not isinstance(close.index, pd.DatetimeIndex):
        close = close.copy()
        close.index = pd.to_datetime(close.index)
    freq = close.index.inferred_freq or "D"

    portfolio = vbt.Portfolio.from_signals(
        close,
        entries=entries,
        exits=exits,
        init_cash=100_000,
        fees=fees,
        slippage=cost_model.slippage_bps / 10_000,
        freq=freq,
    )

    report = build_report(portfolio, strategy.name)
    logger.info(
        "Backtest %s on %s: Sharpe=%.2f, Trades=%d, Return=%.2f%%",
        strategy.name, ticker, report.sharpe_ratio, report.total_trades, report.total_return * 100,
    )

    bias = run_bias_checks(strategy, data, ticker)
    logger.info("Bias checks: look-ahead=%s, survivorship=%s", bias.look_ahead_passed, bias.survivorship_passed)

    wf = walk_forward(strategy, data, n_windows=wf_windows)
    logger.info("Walk-forward: IS=%.2f, OOS=%.2f, degradation=%.1f%%", wf.avg_is_sharpe, wf.avg_oos_sharpe, wf.degradation_pct)

    mc = permutation_test(strategy, data, n_simulations=mc_simulations)
    logger.info("Monte Carlo: actual=%.2f, random=%.2f, p=%.3f, sig=%s", mc.actual_sharpe, mc.mean_random_sharpe, mc.p_value, mc.significant)

    sens: list[SensitivityResult] = []
    if parameters:
        sens = sensitivity_analysis(strategy, data, parameters)

    overfit_flags = detect_overfitting(report.sharpe_ratio, sens, report.total_trades)
    if overfit_flags:
        logger.warning("Overfitting flags: %s", overfit_flags)

    return FullBacktestResult(
        report=report,
        bias_checks=bias,
        walk_forward=wf,
        monte_carlo=mc,
        sensitivity=sens,
        overfitting_flags=overfit_flags,
        cost_model=cost_model,
    )
