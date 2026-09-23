"""Kaabar Ch2 performance metrics: hit ratio, profit factor, risk-reward, equity curve."""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class PatternPerformance:
    pattern_name: str
    total_signals: int
    wins: int
    losses: int
    hit_ratio: float
    profit_factor: float
    avg_rr: float


def evaluate_pattern(
    signals: np.ndarray,
    close: np.ndarray,
    holding_period: int = 5,
) -> PatternPerformance:
    wins = 0
    losses = 0
    total_profit = 0.0
    total_loss = 0.0

    for i in range(len(signals)):
        if signals[i] == 0 or i + holding_period >= len(close):
            continue
        entry = close[i]
        exit_price = close[i + holding_period]
        pnl = (exit_price - entry) * signals[i]
        if pnl > 0:
            wins += 1
            total_profit += pnl
        elif pnl < 0:
            losses += 1
            total_loss += abs(pnl)

    total = wins + losses
    hit_ratio = wins / total if total > 0 else 0.0
    profit_factor = total_profit / total_loss if total_loss > 0 else float("inf") if total_profit > 0 else 0.0
    avg_rr = (total_profit / wins) / (total_loss / losses) if wins > 0 and losses > 0 else 0.0

    return PatternPerformance(
        pattern_name="",
        total_signals=total,
        wins=wins,
        losses=losses,
        hit_ratio=round(hit_ratio, 4),
        profit_factor=round(profit_factor, 4),
        avg_rr=round(avg_rr, 4),
    )
