"""IBKR connector stub — to be implemented after Alpaca is solid."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class IBKRConnector:
    def __init__(self):
        logger.warning("IBKR connector is a stub — not yet implemented")

    def connect(self) -> bool:
        raise NotImplementedError("IBKR connector not yet implemented")

    def submit_order(self, **kwargs) -> dict:
        raise NotImplementedError("IBKR connector not yet implemented")
