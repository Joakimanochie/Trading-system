"""Kaabar Ch2 visualisation: OHLC bars, signal charts, candlestick charts."""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def ohlc_plot_bars(data: np.ndarray, window: int = 100, save_path: str | None = None) -> None:
    d = data[-window:]
    fig, ax = plt.subplots(figsize=(14, 5))
    for i in range(len(d)):
        ax.vlines(i, d[i, 2], d[i, 1], color="black", linewidth=0.8)
        ax.plot(i, d[i, 0], "_", color="black", markersize=4)
        ax.plot(i, d[i, 3], "_", color="black", markersize=4)
    ax.set_title("OHLC Bar Chart")
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def signal_chart(
    data: np.ndarray, signals: np.ndarray, window: int = 100, save_path: str | None = None
) -> None:
    d = data[-window:]
    s = signals[-window:]
    fig, ax = plt.subplots(figsize=(14, 5))
    for i in range(len(d)):
        color = "green" if d[i, 3] >= d[i, 0] else "red"
        ax.vlines(i, d[i, 2], d[i, 1], color=color, linewidth=0.8)
    buys = np.where(s == 1)[0]
    sells = np.where(s == -1)[0]
    ax.scatter(buys, d[buys, 2] * 0.998, marker="^", color="green", s=60, zorder=5)
    ax.scatter(sells, d[sells, 1] * 1.002, marker="v", color="red", s=60, zorder=5)
    ax.set_title("Signal Chart")
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def candlestick_chart(data: np.ndarray, window: int = 100, save_path: str | None = None) -> None:
    d = data[-window:]
    fig, ax = plt.subplots(figsize=(14, 5))
    for i in range(len(d)):
        o, h, l, c = d[i, 0], d[i, 1], d[i, 2], d[i, 3]
        color = "green" if c >= o else "red"
        ax.vlines(i, l, h, color=color, linewidth=0.5)
        body_bottom = min(o, c)
        body_height = abs(c - o)
        rect = mpatches.FancyBboxPatch((i - 0.3, body_bottom), 0.6, body_height, boxstyle="square,pad=0", facecolor=color, edgecolor=color)
        ax.add_patch(rect)
    ax.set_xlim(-1, len(d))
    ax.set_title("Candlestick Chart")
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
