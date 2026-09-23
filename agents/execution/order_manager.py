"""Order lifecycle management: submit, poll, partial fills, retry."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from agents.execution.broker.alpaca import AlpacaConnector, AlpacaOrder

logger = logging.getLogger(__name__)


class OrderState(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass
class ManagedOrder:
    internal_id: str
    broker_order: AlpacaOrder | None = None
    state: OrderState = OrderState.PENDING
    submit_time: datetime | None = None
    fill_time: datetime | None = None
    retries: int = 0
    max_retries: int = 3
    theoretical_price: float = 0.0
    actual_fill_price: float = 0.0


class OrderManager:
    def __init__(self, connector: AlpacaConnector | None = None):
        self.connector = connector or AlpacaConnector()
        self.orders: dict[str, ManagedOrder] = {}

    def submit(
        self,
        internal_id: str,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        theoretical_price: float = 0.0,
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> ManagedOrder:
        managed = ManagedOrder(internal_id=internal_id, theoretical_price=theoretical_price)
        self.orders[internal_id] = managed

        try:
            broker_order = self.connector.submit_order(
                symbol=symbol, qty=qty, side=side, order_type=order_type,
                limit_price=limit_price, stop_price=stop_price,
            )
            managed.broker_order = broker_order
            managed.state = OrderState.SUBMITTED
            managed.submit_time = datetime.utcnow()
            logger.info("Order %s submitted → broker id %s", internal_id, broker_order.id)
        except Exception as e:
            managed.state = OrderState.FAILED
            logger.error("Order %s failed to submit: %s", internal_id, e)

        return managed

    def poll(self, internal_id: str) -> ManagedOrder:
        managed = self.orders.get(internal_id)
        if not managed or not managed.broker_order:
            return managed

        try:
            updated = self.connector.get_order(managed.broker_order.id)
            managed.broker_order = updated

            if updated.status == "filled":
                managed.state = OrderState.FILLED
                managed.fill_time = datetime.utcnow()
                managed.actual_fill_price = updated.filled_avg_price or 0.0
            elif updated.status == "partially_filled":
                managed.state = OrderState.PARTIAL
            elif updated.status in ("cancelled", "expired"):
                managed.state = OrderState.CANCELLED
            elif updated.status == "rejected":
                managed.state = OrderState.REJECTED
        except Exception as e:
            logger.error("Failed to poll order %s: %s", internal_id, e)

        return managed

    def cancel(self, internal_id: str) -> None:
        managed = self.orders.get(internal_id)
        if managed and managed.broker_order and managed.state in (OrderState.SUBMITTED, OrderState.PARTIAL):
            self.connector.cancel_order(managed.broker_order.id)
            managed.state = OrderState.CANCELLED

    def retry(self, internal_id: str) -> ManagedOrder | None:
        managed = self.orders.get(internal_id)
        if not managed or managed.retries >= managed.max_retries:
            return None
        managed.retries += 1
        managed.state = OrderState.PENDING
        logger.info("Retrying order %s (attempt %d/%d)", internal_id, managed.retries, managed.max_retries)
        return managed
