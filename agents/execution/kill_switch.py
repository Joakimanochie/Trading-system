"""Kill switch: halt all orders and optionally flatten all positions."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from agents.execution.broker.alpaca import AlpacaConnector

logger = logging.getLogger(__name__)


@dataclass
class KillSwitchResult:
    orders_cancelled: bool
    positions_closed: bool
    errors: list[str]


def activate_kill_switch(flatten: bool = True, connector: AlpacaConnector | None = None) -> KillSwitchResult:
    """Emergency halt: cancel all orders and optionally close all positions."""
    if connector is None:
        connector = AlpacaConnector()

    errors = []
    orders_cancelled = False
    positions_closed = False

    logger.critical("KILL SWITCH ACTIVATED (flatten=%s)", flatten)

    try:
        connector.cancel_all_orders()
        orders_cancelled = True
        logger.info("All orders cancelled")
    except Exception as e:
        errors.append(f"Failed to cancel orders: {e}")
        logger.error("Failed to cancel orders: %s", e)

    if flatten:
        try:
            connector.close_all_positions()
            positions_closed = True
            logger.info("All positions closed")
        except Exception as e:
            errors.append(f"Failed to close positions: {e}")
            logger.error("Failed to close positions: %s", e)

    return KillSwitchResult(
        orders_cancelled=orders_cancelled,
        positions_closed=positions_closed,
        errors=errors,
    )
