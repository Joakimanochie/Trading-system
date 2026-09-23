"""Monte Carlo permutation significance test for backtests."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
import vectorbt as vbt

from strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


@dataclass
class MonteCarloResult:
    actual_sharpe: float
    mean_random_sharpe: float
    p_value: float
    n_simulations: int
    significant: bool


def permutation_test(
    strategy: BaseStrategy,
    data: pd.DataFrame,
    n_simulations: int = 1000,
    significance: float = 0.05,
) -> MonteCarloResult:
    """Test whether the strategy's Sharpe ratio is statistically significant
    by comparing against randomly permuted signal series."""
    close = data["close"]
    signals = strategy.generate_signals(data)
    entries = signals == 1
    exits = signals == -1

    if entries.sum() == 0:
        return MonteCarloResult(0.0, 0.0, 1.0, n_simulations, False)

    freq = close.index.inferred_freq or "D"
    pf = vbt.Portfolio.from_signals(close, entries=entries, exits=exits, init_cash=100_000, freq=freq)
    actual_sharpe = float(pf.stats().get("Sharpe Ratio", 0))

    random_sharpes: list[float] = []
    signal_values = signals.values.copy()

    for _ in range(n_simulations):
        np.random.shuffle(signal_values)
        rand_signals = pd.Series(signal_values, index=signals.index)
        rand_entries = rand_signals == 1
        rand_exits = rand_signals == -1

        if rand_entries.sum() == 0:
            random_sharpes.append(0.0)
            continue

        rand_pf = vbt.Portfolio.from_signals(close, entries=rand_entries, exits=rand_exits, init_cash=100_000, freq=freq)
        random_sharpes.append(float(rand_pf.stats().get("Sharpe Ratio", 0)))

    mean_random = float(np.mean(random_sharpes))
    p_value = float(np.mean([s >= actual_sharpe for s in random_sharpes]))

    return MonteCarloResult(
        actual_sharpe=round(actual_sharpe, 4),
        mean_random_sharpe=round(mean_random, 4),
        p_value=round(p_value, 4),
        n_simulations=n_simulations,
        significant=p_value < significance,
    )
