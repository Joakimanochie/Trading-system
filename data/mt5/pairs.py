"""CRT pair universe and MT5 symbol helpers."""
from __future__ import annotations

CRT_PAIRS: list[str] = [
    "EURUSD",
    "GBPUSD",
    "USDCHF",
    "USDCAD",
    "AUDUSD",
    "USDJPY",
    "NZDUSD",
    "XAUUSD",   # Gold
    "BTCUSD",   # Bitcoin
    "ETHUSD",   # Ethereum
    "US500",    # S&P 500 CFD (broker-dependent symbol)
    "UK100",    # FTSE 100 CFD (broker-dependent symbol)
]

# Pairs with 3-decimal-place pip values (JPY pairs)
JPY_PAIRS: set[str] = {"USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY"}


def pip_value(symbol: str) -> float:
    """Return pip size for the given symbol."""
    if symbol in JPY_PAIRS or symbol.endswith("JPY"):
        return 0.01
    if symbol in ("XAUUSD",):
        return 0.01
    if symbol.startswith("BTC") or symbol.startswith("ETH"):
        return 1.0
    return 0.0001
