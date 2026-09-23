"""Photon Module 1: Structure Engine — fractal swings, HH/HL/LH/LL labelling, Strong/Weak classification."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from agents.shared.market.swings import detect_swings, label_structure, SwingPoint


@dataclass
class StructureLevel:
    swing: SwingPoint
    label: str  # HH, HL, LH, LL
    strong: bool  # Strong = defended by subsequent structure


def classify_strong_weak(labelled: list[tuple[SwingPoint, str]]) -> list[StructureLevel]:
    """Classify swing points as Strong or Weak.

    Strong Low = a low that produced a subsequent Higher High (institutions defended it).
    Weak Low = failed to produce a new HH.
    Strong High = produced a subsequent Lower Low. Weak High = failed.
    """
    levels: list[StructureLevel] = []
    for i, (swing, label) in enumerate(labelled):
        strong = False
        if swing.swing_type == "low":
            for j in range(i + 1, len(labelled)):
                future_swing, future_label = labelled[j]
                if future_swing.swing_type == "high":
                    if future_label == "HH":
                        strong = True
                    break
        elif swing.swing_type == "high":
            for j in range(i + 1, len(labelled)):
                future_swing, future_label = labelled[j]
                if future_swing.swing_type == "low":
                    if future_label == "LL":
                        strong = True
                    break
        levels.append(StructureLevel(swing=swing, label=label, strong=strong))
    return levels


def analyze_structure(
    data: pd.DataFrame,
    fractal_n: int = 2,
) -> list[StructureLevel]:
    """Full structure analysis: detect swings, label, classify Strong/Weak."""
    swings = detect_swings(data, fractal_n)
    labelled = label_structure(swings)
    return classify_strong_weak(labelled)
