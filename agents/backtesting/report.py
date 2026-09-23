"""Backtest report generation from vectorbt portfolio results."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass
class BacktestReport:
    strategy_name: str
    period_start: datetime
    period_end: datetime
    sharpe_ratio: float = 0.0
    calmar_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    max_drawdown_duration_days: int = 0
    cagr: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_trade_duration_mins: float = 0.0
    total_trades: int = 0
    total_return: float = 0.0
    equity_curve: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


def build_report(portfolio, strategy_name: str) -> BacktestReport:
    """Extract a BacktestReport from a vectorbt Portfolio object."""
    stats = portfolio.stats()

    returns = portfolio.returns()
    equity = portfolio.value()

    max_dd = float(stats.get("Max Drawdown [%]", 0)) / 100
    raw_dd_dur = stats.get("Max Drawdown Duration", 0)
    if isinstance(raw_dd_dur, pd.Timedelta):
        dd_duration_days = raw_dd_dur.days
    else:
        dd_duration_days = int(raw_dd_dur) if raw_dd_dur else 0

    trades = portfolio.trades
    n_trades = int(stats.get("Total Trades", 0))
    win_rate = float(stats.get("Win Rate [%]", 0)) / 100

    winning_pnl = 0.0
    losing_pnl = 0.0
    total_trade_duration = 0.0
    if n_trades > 0 and hasattr(trades, "records_readable"):
        recs = trades.records_readable
        if "PnL" in recs.columns:
            wins = recs[recs["PnL"] > 0]["PnL"].sum()
            losses = abs(recs[recs["PnL"] < 0]["PnL"].sum())
            winning_pnl = float(wins)
            losing_pnl = float(losses)
        if "Duration" in recs.columns:
            durations = pd.to_timedelta(recs["Duration"])
            total_trade_duration = durations.mean().total_seconds() / 60 if len(durations) > 0 else 0

    profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else float("inf") if winning_pnl > 0 else 0.0

    total_return = float(stats.get("Total Return [%]", 0)) / 100
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 0.01)
    cagr = (1 + total_return) ** (1 / years) - 1 if total_return > -1 else -1.0

    sharpe = float(stats.get("Sharpe Ratio", 0))
    sortino = float(stats.get("Sortino Ratio", 0))
    calmar = abs(cagr / max_dd) if max_dd > 0 else 0.0

    eq_values = equity.tolist()
    step = max(1, len(eq_values) // 500)
    sampled_eq = eq_values[::step]

    return BacktestReport(
        strategy_name=strategy_name,
        period_start=equity.index[0].to_pydatetime(),
        period_end=equity.index[-1].to_pydatetime(),
        sharpe_ratio=round(sharpe, 4),
        calmar_ratio=round(calmar, 4),
        sortino_ratio=round(sortino, 4),
        max_drawdown_pct=round(max_dd, 6),
        max_drawdown_duration_days=dd_duration_days,
        cagr=round(cagr, 6),
        win_rate=round(win_rate, 4),
        profit_factor=round(profit_factor, 4),
        avg_trade_duration_mins=round(total_trade_duration, 2),
        total_trades=n_trades,
        total_return=round(total_return, 6),
        equity_curve=sampled_eq,
    )
