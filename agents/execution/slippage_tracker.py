"""Slippage tracker: actual fill vs theoretical price, logged per order."""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SlippageRecord:
    order_id: str
    symbol: str
    side: str
    theoretical_price: float
    actual_price: float
    slippage_bps: float
    slippage_dollars: float


def compute_slippage(
    order_id: str,
    symbol: str,
    side: str,
    theoretical_price: float,
    actual_price: float,
    qty: float,
) -> SlippageRecord:
    """Compute slippage between theoretical and actual fill price."""
    if theoretical_price == 0:
        slippage_bps = 0.0
    elif side == "buy":
        slippage_bps = (actual_price - theoretical_price) / theoretical_price * 10_000
    else:
        slippage_bps = (theoretical_price - actual_price) / theoretical_price * 10_000

    slippage_dollars = abs(actual_price - theoretical_price) * qty

    record = SlippageRecord(
        order_id=order_id,
        symbol=symbol,
        side=side,
        theoretical_price=round(theoretical_price, 6),
        actual_price=round(actual_price, 6),
        slippage_bps=round(slippage_bps, 2),
        slippage_dollars=round(slippage_dollars, 2),
    )

    logger.info(
        "Slippage %s %s: theoretical=%.6f actual=%.6f slip=%.1f bps ($%.2f)",
        symbol, side, theoretical_price, actual_price, slippage_bps, slippage_dollars,
    )
    return record
