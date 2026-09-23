"""Regime detection: volatility shifts, correlation drift, VIX levels."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class RegimeState:
    volatility_regime: str  # "normal", "elevated", "crisis"
    volatility_ratio: float  # current / backtest average
    correlation_drift: float
    vix_level: float | None
    regime_shift_detected: bool
    details: list[str]


def detect_regime(
    returns: pd.Series,
    backtest_vol: float,
    backtest_correlation: float | None = None,
    benchmark_returns: pd.Series | None = None,
    vix_level: float | None = None,
    window: int = 30,
) -> RegimeState:
    """Detect regime shifts by comparing rolling metrics to backtest baselines."""
    details = []

    # Rolling volatility vs backtest
    rolling_vol = returns.rolling(window).std().iloc[-1] if len(returns) >= window else returns.std()
    vol_ratio = rolling_vol / backtest_vol if backtest_vol > 0 else 1.0

    if vol_ratio > 2.0:
        vol_regime = "crisis"
        details.append(f"Volatility {vol_ratio:.1f}x backtest average — crisis level")
    elif vol_ratio > 1.5:
        vol_regime = "elevated"
        details.append(f"Volatility {vol_ratio:.1f}x backtest average — elevated")
    else:
        vol_regime = "normal"

    # Correlation drift
    corr_drift = 0.0
    if benchmark_returns is not None and backtest_correlation is not None and len(returns) >= window:
        aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(aligned) >= window:
            rolling_corr = aligned.iloc[-window:].corr().iloc[0, 1]
            corr_drift = abs(rolling_corr - backtest_correlation)
            if corr_drift > 0.3:
                details.append(f"Correlation drift {corr_drift:.2f} from backtest")

    # VIX
    if vix_level is not None and vix_level > 30:
        details.append(f"VIX at {vix_level:.1f} — elevated fear")

    shift = vol_regime != "normal" or corr_drift > 0.3 or (vix_level is not None and vix_level > 30)

    if shift:
        logger.warning("REGIME SHIFT detected: %s", details)

    return RegimeState(
        volatility_regime=vol_regime,
        volatility_ratio=round(vol_ratio, 4),
        correlation_drift=round(corr_drift, 4),
        vix_level=vix_level,
        regime_shift_detected=shift,
        details=details,
    )
