"""Abstract base class for all strategies."""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    """Every strategy must implement generate_signals()."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Given OHLCV data, return a signal series where:
            +1 = long entry
            -1 = short entry
             0 = no signal / exit
        Index must match data.index.
        """
        ...

    def __repr__(self) -> str:
        return f"<Strategy: {self.name}>"
