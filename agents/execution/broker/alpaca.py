"""Alpaca broker connector: paper + live mode."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class AlpacaOrder:
    id: str
    symbol: str
    side: str
    qty: float
    filled_qty: float
    status: str
    filled_avg_price: float | None = None


class AlpacaConnector:
    def __init__(self):
        self.base_url = settings.alpaca_base_url
        self.headers = {
            "APCA-API-KEY-ID": settings.alpaca_api_key,
            "APCA-API-SECRET-KEY": settings.alpaca_secret_key,
        }

    def _get(self, path: str) -> dict:
        resp = requests.get(f"{self.base_url}{path}", headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, data: dict) -> dict:
        resp = requests.post(f"{self.base_url}{path}", json=data, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str) -> dict | None:
        resp = requests.delete(f"{self.base_url}{path}", headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json() if resp.text else None

    def get_account(self) -> dict:
        return self._get("/v2/account")

    def get_positions(self) -> list[dict]:
        return self._get("/v2/positions")

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        time_in_force: str = "gtc",
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> AlpacaOrder:
        payload = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
        }
        if limit_price is not None:
            payload["limit_price"] = str(limit_price)
        if stop_price is not None:
            payload["stop_price"] = str(stop_price)

        data = self._post("/v2/orders", payload)
        logger.info("Order submitted: %s %s %s qty=%s", side, symbol, order_type, qty)
        return AlpacaOrder(
            id=data["id"],
            symbol=data["symbol"],
            side=data["side"],
            qty=float(data["qty"]),
            filled_qty=float(data.get("filled_qty", 0)),
            status=data["status"],
            filled_avg_price=float(data["filled_avg_price"]) if data.get("filled_avg_price") else None,
        )

    def get_order(self, order_id: str) -> AlpacaOrder:
        data = self._get(f"/v2/orders/{order_id}")
        return AlpacaOrder(
            id=data["id"],
            symbol=data["symbol"],
            side=data["side"],
            qty=float(data["qty"]),
            filled_qty=float(data.get("filled_qty", 0)),
            status=data["status"],
            filled_avg_price=float(data["filled_avg_price"]) if data.get("filled_avg_price") else None,
        )

    def cancel_order(self, order_id: str) -> None:
        self._delete(f"/v2/orders/{order_id}")
        logger.info("Order cancelled: %s", order_id)

    def cancel_all_orders(self) -> None:
        self._delete("/v2/orders")
        logger.warning("ALL orders cancelled")

    def close_all_positions(self) -> None:
        self._delete("/v2/positions")
        logger.warning("ALL positions closed")
