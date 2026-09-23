"""Binance connector stub — for crypto expansion."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class BinanceConnector:
    def __init__(self):
        logger.warning("Binance connector is a stub — not yet implemented")

    def connect(self) -> bool:
        raise NotImplementedError("Binance connector not yet implemented")

    def submit_order(self, **kwargs) -> dict:
        raise NotImplementedError("Binance connector not yet implemented")
