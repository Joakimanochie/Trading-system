"""Kaabar Ch2 primal array manipulation functions."""
from __future__ import annotations

import numpy as np


def add_column(data: np.ndarray, times: int = 1) -> np.ndarray:
    for _ in range(times):
        data = np.append(data, np.zeros((data.shape[0], 1)), axis=1)
    return data


def delete_column(data: np.ndarray, index: int, times: int = 1) -> np.ndarray:
    for i in range(times):
        data = np.delete(data, index, axis=1)
    return data


def add_row(data: np.ndarray, times: int = 1) -> np.ndarray:
    for _ in range(times):
        data = np.append(data, np.zeros((1, data.shape[1])), axis=0)
    return data


def delete_row(data: np.ndarray, number: int = 1) -> np.ndarray:
    return data[number:]


def rounding(data: np.ndarray, how_far: int = 5) -> np.ndarray:
    return np.round(data, how_far)
