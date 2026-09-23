"""Photon chart exporter: annotated PNG with structure, POIs, liquidity, levels."""
from __future__ import annotations

import os
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

from agents.photon.signal_builder import PhotonSignal
from agents.photon.structure_engine import StructureLevel
from agents.photon.liquidity_map import LiquidityPool


def export_chart(
    signal: PhotonSignal,
    h4_data: pd.DataFrame,
    ltf_data: pd.DataFrame,
    levels: list[StructureLevel] | None = None,
    pools: list[LiquidityPool] | None = None,
    output_dir: str = "charts",
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"photon_{signal.pair}_{signal.direction}_{ts}.png"
    filepath = os.path.join(output_dir, filename)

    fig, (ax_h4, ax_ltf) = plt.subplots(2, 1, figsize=(14, 10))

    _draw_candles(ax_h4, h4_data.tail(30), f"{signal.pair} H4 — Structure")

    if levels:
        for lv in levels[-10:]:
            color = "green" if lv.label in ("HH", "HL") else "red"
            style = "-" if lv.strong else ":"
            ax_h4.axhline(lv.swing.price, color=color, linestyle=style, linewidth=0.7, alpha=0.6)

    if pools:
        for p in pools[:10]:
            color = "blue" if p.pool_type == "BSL" else "orange"
            ax_h4.axhline(p.price, color=color, linestyle="--", linewidth=0.5, alpha=0.4)

    ax_h4.legend(loc="upper left", fontsize=8)

    _draw_candles(ax_ltf, ltf_data.tail(40), f"{signal.pair} LTF — Entry Detail")
    lv = signal.levels
    ax_ltf.axhline(lv.entry, color="green", linewidth=1.5, label=f"Entry {lv.entry:.5f}")
    ax_ltf.axhline(lv.sl, color="red", linewidth=1, label=f"SL {lv.sl:.5f}")
    ax_ltf.axhline(lv.tp1, color="orange", linestyle="--", label=f"TP1 {lv.tp1:.5f}")
    ax_ltf.axhline(lv.tp2, color="purple", linestyle="--", label=f"TP2 {lv.tp2:.5f}")
    ax_ltf.legend(loc="upper left", fontsize=8)

    fig.suptitle(
        f"Alignment: {signal.alignment.score}/4 | R:R: {signal.rr:.1f} | Basis: {signal.entry_basis}",
        fontsize=10, y=0.02,
    )
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return filepath


def _draw_candles(ax, data: pd.DataFrame, title: str) -> None:
    ax.set_title(title, fontsize=11)
    for i in range(len(data)):
        o, h, l, c = float(data.iloc[i]["open"]), float(data.iloc[i]["high"]), float(data.iloc[i]["low"]), float(data.iloc[i]["close"])
        color = "green" if c >= o else "red"
        ax.vlines(i, l, h, color=color, linewidth=0.5)
        rect = mpatches.FancyBboxPatch((i - 0.3, min(o, c)), 0.6, abs(c - o), boxstyle="square,pad=0", facecolor=color, edgecolor=color)
        ax.add_patch(rect)
    ax.set_xlim(-1, len(data))
