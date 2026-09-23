"""CRT Chart Exporter: generate annotated PNG chart per signal."""
from __future__ import annotations

import os
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

from agents.crt.signal_builder import CRTSignalData


def export_chart(signal: CRTSignalData, htf_data: pd.DataFrame, ltf_data: pd.DataFrame, output_dir: str = "charts") -> str:
    """Generate and save an annotated chart for a CRT signal. Returns the file path."""
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"crt_{signal.pair}_{signal.direction}_{ts}.png"
    filepath = os.path.join(output_dir, filename)

    fig, (ax_htf, ax_ltf) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={"height_ratios": [1, 1]})

    _draw_candlesticks(ax_htf, htf_data.tail(20), f"{signal.pair} {signal.htf} — CRT Setup")
    a = signal.anchor
    ax_htf.axhline(a.crt_high, color="red", linestyle="--", linewidth=1, label=f"CRT-High {a.crt_high:.5f}")
    ax_htf.axhline(a.crt_low, color="blue", linestyle="--", linewidth=1, label=f"CRT-Low {a.crt_low:.5f}")
    ax_htf.axhline(a.crt_eq, color="gray", linestyle=":", linewidth=1, label=f"EQ {a.crt_eq:.5f}")
    ax_htf.legend(loc="upper left", fontsize=8)

    _draw_candlesticks(ax_ltf, ltf_data.tail(40), f"{signal.pair} {signal.ltf} — Entry Detail")
    lv = signal.levels
    ax_ltf.axhline(lv.entry, color="green", linewidth=1.5, label=f"Entry {lv.entry:.5f}")
    ax_ltf.axhline(lv.sl_conservative, color="red", linewidth=1, label=f"SL {lv.sl_conservative:.5f}")
    ax_ltf.axhline(lv.tp1, color="orange", linewidth=1, linestyle="--", label=f"TP1 {lv.tp1:.5f}")
    ax_ltf.axhline(lv.tp2, color="purple", linewidth=1, linestyle="--", label=f"TP2 {lv.tp2:.5f}")

    if signal.mss.fvg_high and signal.mss.fvg_low:
        ax_ltf.axhspan(signal.mss.fvg_low, signal.mss.fvg_high, alpha=0.15, color="cyan", label="FVG")

    ax_ltf.legend(loc="upper left", fontsize=8)

    filter_text = (
        f"Filters: {signal.filters.passed_count}/5 | "
        f"Confluence: {signal.confluence_score} ({', '.join(signal.confluence_patterns[:3]) or 'none'})"
    )
    fig.suptitle(filter_text, fontsize=10, y=0.02)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return filepath


def _draw_candlesticks(ax, data: pd.DataFrame, title: str) -> None:
    ax.set_title(title, fontsize=11)
    for i in range(len(data)):
        o = float(data.iloc[i]["open"])
        h = float(data.iloc[i]["high"])
        l = float(data.iloc[i]["low"])
        c = float(data.iloc[i]["close"])
        color = "green" if c >= o else "red"
        ax.vlines(i, l, h, color=color, linewidth=0.5)
        body_bottom = min(o, c)
        body_height = abs(c - o)
        rect = mpatches.FancyBboxPatch(
            (i - 0.3, body_bottom), 0.6, body_height,
            boxstyle="square,pad=0", facecolor=color, edgecolor=color,
        )
        ax.add_patch(rect)
    ax.set_xlim(-1, len(data))
