"""Cross-sectional momentum strategy: long when price is above N-day SMA, short when below."""
from __future__ import annotations

import pandas as pd

from strategies.base import BaseStrategy


class MomentumStrategy(BaseStrategy):
    name = "momentum_sma_crossover"
    description = "Long when close > SMA(lookback), short when close < SMA(lookback)"

    def __init__(self, lookback: int = 20):
        self.lookback = int(lookback)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        sma = close.rolling(window=self.lookback).mean()

        signals = pd.Series(0, index=data.index)
        signals[close > sma] = 1
        signals[close < sma] = -1
        signals.iloc[: self.lookback] = 0
        return signals
