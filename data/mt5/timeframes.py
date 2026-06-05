"""MT5 timeframe constants and string-to-constant mapping."""
from __future__ import annotations

# Lazy import — MetaTrader5 is Windows-only and may not be installed in all environments.
# Callers should guard with a try/except or check MT5_ENABLED.

_TF_MAP: dict[str, int] | None = None


def get_timeframe_map() -> dict[str, int]:
    global _TF_MAP
    if _TF_MAP is not None:
        return _TF_MAP

    import MetaTrader5 as mt5  # type: ignore[import]

    _TF_MAP = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "MN": mt5.TIMEFRAME_MN1,
    }
    return _TF_MAP


def resolve_timeframe(name: str) -> int:
    """Convert a string timeframe name (e.g. 'H4') to the MT5 constant integer."""
    tf_map = get_timeframe_map()
    if name not in tf_map:
        raise ValueError(f"Unknown timeframe '{name}'. Valid: {list(tf_map.keys())}")
    return tf_map[name]
