"""Position sizer: Kelly leverage → dollar size and units."""
from __future__ import annotations

from dataclasses import dataclass

from agents.risk.kelly import fractional_kelly


@dataclass
class PositionSize:
    kelly_fraction: float
    risk_dollars: float
    position_dollars: float
    units: float


def size_position(
    capital: float,
    win_rate: float,
    profit_factor: float,
    entry_price: float,
    stop_loss: float,
    kelly_frac_override: float | None = None,
) -> PositionSize:
    """Compute position size from Kelly fraction and stop-loss distance.

    Returns the dollar amount to allocate and the number of units to trade.
    """
    fk = fractional_kelly(win_rate, profit_factor, kelly_frac_override)
    risk_dollars = capital * fk

    sl_distance = abs(entry_price - stop_loss)
    if sl_distance == 0:
        return PositionSize(fk, risk_dollars, 0.0, 0.0)

    units = risk_dollars / sl_distance
    position_dollars = units * entry_price

    return PositionSize(
        kelly_fraction=round(fk, 6),
        risk_dollars=round(risk_dollars, 2),
        position_dollars=round(position_dollars, 2),
        units=round(units, 4),
    )


def allocate_portfolio(
    capital: float,
    strategies: list[dict],
) -> list[dict]:
    """Allocate capital across N strategies using inverse-variance weighting.

    Each strategy dict must have: name, returns_std (std dev of returns).
    Returns list of dicts with name and allocation_pct.
    """
    if not strategies:
        return []

    inv_vars = []
    for s in strategies:
        std = s.get("returns_std", 1.0)
        inv_vars.append(1.0 / (std ** 2) if std > 0 else 0.0)

    total = sum(inv_vars) or 1.0
    result = []
    for s, iv in zip(strategies, inv_vars):
        pct = iv / total
        result.append({
            "name": s["name"],
            "allocation_pct": round(pct, 4),
            "allocation_dollars": round(capital * pct, 2),
        })
    return result
