"""Strategy degradation detection: rolling live Sharpe vs backtest Sharpe."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DegradationResult:
    strategy_name: str
    live_sharpe: float
    backtest_sharpe: float
    ratio: float  # live / backtest
    degraded: bool
    threshold: float


def check_degradation(
    strategy_name: str,
    live_returns: pd.Series,
    backtest_sharpe: float,
    threshold: float = 0.5,
    window: int = 60,
    annualization: float = 252,
) -> DegradationResult:
    """Alert if rolling live Sharpe falls below threshold * backtest Sharpe."""
    if len(live_returns) < window or backtest_sharpe <= 0:
        return DegradationResult(strategy_name, 0.0, backtest_sharpe, 0.0, False, threshold)

    recent = live_returns.iloc[-window:]
    mean = recent.mean() * annualization
    std = recent.std() * np.sqrt(annualization)
    live_sharpe = mean / std if std > 0 else 0.0

    ratio = live_sharpe / backtest_sharpe if backtest_sharpe > 0 else 0.0
    degraded = ratio < threshold

    if degraded:
        logger.warning(
            "DEGRADATION: %s live Sharpe %.2f is %.0f%% of backtest %.2f (threshold %.0f%%)",
            strategy_name, live_sharpe, ratio * 100, backtest_sharpe, threshold * 100,
        )

    return DegradationResult(
        strategy_name=strategy_name,
        live_sharpe=round(live_sharpe, 4),
        backtest_sharpe=round(backtest_sharpe, 4),
        ratio=round(ratio, 4),
        degraded=degraded,
        threshold=threshold,
    )
