"""Kaabar technical indicators: MA, ATR, RSI, Stochastic, TII, K's Vol Bands."""
from __future__ import annotations

import numpy as np


def ma(data: np.ndarray, lookback: int, close_col: int = 3, position: int | None = None) -> np.ndarray:
    if position is None:
        from agents.crt.kaabar.primal import add_column
        data = add_column(data)
        position = data.shape[1] - 1
    for i in range(lookback, len(data)):
        data[i, position] = np.mean(data[i - lookback + 1 : i + 1, close_col])
    return data


def smoothed_ma(data: np.ndarray, lookback: int, close_col: int = 3, position: int | None = None) -> np.ndarray:
    if position is None:
        from agents.crt.kaabar.primal import add_column
        data = add_column(data)
        position = data.shape[1] - 1
    data[lookback - 1, position] = np.mean(data[:lookback, close_col])
    for i in range(lookback, len(data)):
        data[i, position] = (data[i - 1, position] * (lookback - 1) + data[i, close_col]) / lookback
    return data


def atr(
    data: np.ndarray,
    lookback: int = 14,
    high_col: int = 1,
    low_col: int = 2,
    close_col: int = 3,
    position: int | None = None,
) -> np.ndarray:
    if position is None:
        from agents.crt.kaabar.primal import add_column
        data = add_column(data)
        position = data.shape[1] - 1
    for i in range(1, len(data)):
        tr = max(
            data[i, high_col] - data[i, low_col],
            abs(data[i, high_col] - data[i - 1, close_col]),
            abs(data[i, low_col] - data[i - 1, close_col]),
        )
        data[i, position] = tr
    data = smoothed_ma(data, lookback, position, position)
    return data


def rsi(data: np.ndarray, lookback: int = 14, close_col: int = 3, position: int | None = None) -> np.ndarray:
    if position is None:
        from agents.crt.kaabar.primal import add_column
        data = add_column(data)
        position = data.shape[1] - 1
    deltas = np.diff(data[:, close_col])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[:lookback])
    avg_loss = np.mean(losses[:lookback])

    for i in range(lookback, len(deltas)):
        avg_gain = (avg_gain * (lookback - 1) + gains[i]) / lookback
        avg_loss = (avg_loss * (lookback - 1) + losses[i]) / lookback
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        data[i + 1, position] = 100 - 100 / (1 + rs)

    return data


def stochastic(
    data: np.ndarray,
    lookback: int = 14,
    high_col: int = 1,
    low_col: int = 2,
    close_col: int = 3,
    position: int | None = None,
) -> np.ndarray:
    if position is None:
        from agents.crt.kaabar.primal import add_column
        data = add_column(data)
        position = data.shape[1] - 1
    for i in range(lookback, len(data)):
        highest = np.max(data[i - lookback + 1 : i + 1, high_col])
        lowest = np.min(data[i - lookback + 1 : i + 1, low_col])
        if highest - lowest > 0:
            data[i, position] = ((data[i, close_col] - lowest) / (highest - lowest)) * 100
    return data


def trend_intensity_indicator(
    data: np.ndarray, lookback: int = 20, close_col: int = 3, position: int | None = None
) -> np.ndarray:
    if position is None:
        from agents.crt.kaabar.primal import add_column
        data = add_column(data)
        position = data.shape[1] - 1
    data = ma(data, lookback, close_col, position)
    from agents.crt.kaabar.primal import add_column
    data = add_column(data)
    tii_pos = data.shape[1] - 1
    for i in range(lookback, len(data)):
        above = sum(1 for j in range(i - lookback + 1, i + 1) if data[j, close_col] > data[j, position])
        data[i, tii_pos] = (above / lookback) * 100
    return data


def k_volatility_band(
    data: np.ndarray,
    lookback: int = 20,
    multiplier: float = 2.0,
    high_col: int = 1,
    low_col: int = 2,
    close_col: int = 3,
    position: int | None = None,
) -> np.ndarray:
    from agents.crt.kaabar.primal import add_column
    if position is None:
        data = add_column(data, 3)
        position = data.shape[1] - 3
    data = ma(data, lookback, close_col, position)
    atr_pos = position + 1
    upper_pos = position + 2
    data = atr(data, lookback, high_col, low_col, close_col, atr_pos)
    for i in range(lookback, len(data)):
        data[i, upper_pos] = data[i, position] + multiplier * data[i, atr_pos]
    return data
