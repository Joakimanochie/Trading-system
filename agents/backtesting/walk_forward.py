"""Walk-forward analysis: rolling in-sample / out-of-sample windows."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd
import vectorbt as vbt

from strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardResult:
    in_sample_sharpes: list[float]
    out_of_sample_sharpes: list[float]
    avg_is_sharpe: float
    avg_oos_sharpe: float
    degradation_pct: float
    n_windows: int


def walk_forward(
    strategy: BaseStrategy,
    data: pd.DataFrame,
    n_windows: int = 5,
    oos_pct: float = 0.2,
) -> WalkForwardResult:
    """Run rolling walk-forward analysis.

    Splits data into `n_windows` sequential segments. For each, uses the
    leading portion as in-sample and the trailing `oos_pct` as out-of-sample.
    """
    close = data["close"]
    total_len = len(data)
    window_size = total_len // n_windows

    is_sharpes: list[float] = []
    oos_sharpes: list[float] = []

    for i in range(n_windows):
        start = i * window_size
        end = min(start + window_size, total_len)
        window_data = data.iloc[start:end]

        oos_start = int(len(window_data) * (1 - oos_pct))
        is_data = window_data.iloc[:oos_start]
        oos_data = window_data.iloc[oos_start:]

        if len(is_data) < 20 or len(oos_data) < 10:
            continue

        def _sharpe(d: pd.DataFrame) -> float:
            signals = strategy.generate_signals(d)
            entries = signals == 1
            exits = signals == -1
            if entries.sum() == 0:
                return 0.0
            freq = d["close"].index.inferred_freq or "D"
            pf = vbt.Portfolio.from_signals(d["close"], entries=entries, exits=exits, init_cash=100_000, freq=freq)
            return float(pf.stats().get("Sharpe Ratio", 0))

        is_s = _sharpe(is_data)
        oos_s = _sharpe(oos_data)
        is_sharpes.append(is_s)
        oos_sharpes.append(oos_s)

    avg_is = sum(is_sharpes) / len(is_sharpes) if is_sharpes else 0.0
    avg_oos = sum(oos_sharpes) / len(oos_sharpes) if oos_sharpes else 0.0
    degradation = (1 - avg_oos / avg_is) * 100 if avg_is != 0 else 0.0

    return WalkForwardResult(
        in_sample_sharpes=is_sharpes,
        out_of_sample_sharpes=oos_sharpes,
        avg_is_sharpe=round(avg_is, 4),
        avg_oos_sharpe=round(avg_oos, 4),
        degradation_pct=round(degradation, 2),
        n_windows=len(is_sharpes),
    )
