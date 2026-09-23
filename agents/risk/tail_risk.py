"""Tail risk stress testing: loss at N-sigma and worst historical moves."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class TailRiskReport:
    sigma_3_loss: float
    sigma_5_loss: float
    worst_1d_loss: float
    worst_1d_date: str
    var_95: float
    var_99: float


def stress_test(returns: pd.Series, capital: float = 100_000) -> TailRiskReport:
    """Run tail risk stress test on a returns series."""
    mean = returns.mean()
    std = returns.std()

    sigma_3 = mean - 3 * std
    sigma_5 = mean - 5 * std

    worst_idx = returns.idxmin()
    worst_val = returns.min()

    var_95 = float(np.percentile(returns, 5))
    var_99 = float(np.percentile(returns, 1))

    return TailRiskReport(
        sigma_3_loss=round(sigma_3 * capital, 2),
        sigma_5_loss=round(sigma_5 * capital, 2),
        worst_1d_loss=round(worst_val * capital, 2),
        worst_1d_date=str(worst_idx),
        var_95=round(var_95 * capital, 2),
        var_99=round(var_99 * capital, 2),
    )
