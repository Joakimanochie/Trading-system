"""Position reconciler: compare internal positions to broker positions."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from agents.execution.broker.alpaca import AlpacaConnector

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationResult:
    matched: bool
    mismatches: list[dict]


def reconcile(
    internal_positions: dict[str, float],
    connector: AlpacaConnector | None = None,
) -> ReconciliationResult:
    """Compare internal position map {symbol: qty} against broker.

    Returns matched=True if all positions align, otherwise lists mismatches.
    """
    if connector is None:
        connector = AlpacaConnector()

    broker_positions = connector.get_positions()
    broker_map = {p["symbol"]: float(p["qty"]) for p in broker_positions}

    mismatches = []
    all_symbols = set(list(internal_positions.keys()) + list(broker_map.keys()))

    for sym in all_symbols:
        internal_qty = internal_positions.get(sym, 0.0)
        broker_qty = broker_map.get(sym, 0.0)
        if abs(internal_qty - broker_qty) > 0.001:
            mismatch = {
                "symbol": sym,
                "internal_qty": internal_qty,
                "broker_qty": broker_qty,
                "diff": round(internal_qty - broker_qty, 4),
            }
            mismatches.append(mismatch)
            logger.warning("POSITION MISMATCH: %s internal=%s broker=%s", sym, internal_qty, broker_qty)

    if mismatches:
        logger.warning("Reconciliation found %d mismatches", len(mismatches))
    else:
        logger.info("Reconciliation passed — all positions match")

    return ReconciliationResult(matched=len(mismatches) == 0, mismatches=mismatches)
