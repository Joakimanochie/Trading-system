"""Parameter sensitivity analysis: vary each parameter ±20%, log Sharpe degradation."""
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass

import pandas as pd
import vectorbt as vbt

from strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


@dataclass
class SensitivityResult:
    parameter_name: str
    base_value: float
    low_value: float
    high_value: float
    base_sharpe: float
    low_sharpe: float
    high_sharpe: float
    max_degradation_pct: float


def sensitivity_analysis(
    strategy: BaseStrategy,
    data: pd.DataFrame,
    parameters: dict[str, float],
    variation: float = 0.2,
) -> list[SensitivityResult]:
    """Vary each parameter ±variation (default ±20%) and measure Sharpe change.

    `parameters` maps parameter name → current value. The strategy must
    accept these as attributes that can be set directly.
    """
    close = data["close"]

    def _sharpe(strat: BaseStrategy) -> float:
        signals = strat.generate_signals(data)
        entries = signals == 1
        exits = signals == -1
        if entries.sum() == 0:
            return 0.0
        freq = close.index.inferred_freq or "D"
        pf = vbt.Portfolio.from_signals(close, entries=entries, exits=exits, init_cash=100_000, freq=freq)
        return float(pf.stats().get("Sharpe Ratio", 0))

    base_sharpe = _sharpe(strategy)
    results: list[SensitivityResult] = []

    for param_name, base_val in parameters.items():
        low_val = base_val * (1 - variation)
        high_val = base_val * (1 + variation)

        strat_low = copy.deepcopy(strategy)
        current_type = type(getattr(strat_low, param_name, low_val))
        setattr(strat_low, param_name, current_type(low_val))
        low_sharpe = _sharpe(strat_low)

        strat_high = copy.deepcopy(strategy)
        setattr(strat_high, param_name, current_type(high_val))
        high_sharpe = _sharpe(strat_high)

        worst_sharpe = min(low_sharpe, high_sharpe)
        degradation = (1 - worst_sharpe / base_sharpe) * 100 if base_sharpe != 0 else 0.0

        results.append(SensitivityResult(
            parameter_name=param_name,
            base_value=base_val,
            low_value=low_val,
            high_value=high_val,
            base_sharpe=round(base_sharpe, 4),
            low_sharpe=round(low_sharpe, 4),
            high_sharpe=round(high_sharpe, 4),
            max_degradation_pct=round(degradation, 2),
        ))

    return results


def detect_overfitting(
    base_sharpe: float,
    sensitivity_results: list[SensitivityResult],
    total_trades: int,
    min_trades: int = 100,
) -> list[str]:
    """Flag overfitting indicators."""
    flags: list[str] = []

    if base_sharpe > 3.0:
        flags.append(f"Pre-cost Sharpe > 3 ({base_sharpe:.2f}) — likely overfit")

    for r in sensitivity_results:
        if r.max_degradation_pct > 80:
            flags.append(
                f"Parameter '{r.parameter_name}' causes {r.max_degradation_pct:.0f}% Sharpe collapse — one-point wonder"
            )

    if total_trades < min_trades:
        flags.append(f"Only {total_trades} trades (minimum {min_trades}) — insufficient sample")

    return flags
