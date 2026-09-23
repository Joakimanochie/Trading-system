"""Photon Module 6: Expectational Orderflow (EOF) Engine — the signature Photon step.

Creates anticipatory Expectation objects when new structural extremes form.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from agents.photon.poi_detector import POI
from agents.photon.structure_engine import StructureLevel


class ExpectationStatus(str, Enum):
    PENDING = "PENDING"
    PRICE_ARRIVED = "PRICE_ARRIVED"
    TRIGGERED = "TRIGGERED"
    EXPIRED = "EXPIRED"


@dataclass
class Expectation:
    id: str
    pair: str
    direction: str  # "LONG" or "SHORT"
    anticipated_poi: POI | None
    anticipated_price_zone: tuple[float, float]  # (low, high)
    created_at: datetime
    status: ExpectationStatus = ExpectationStatus.PENDING
    arrived_at: datetime | None = None
    triggered_at: datetime | None = None
    expired_reason: str | None = None


class EOFEngine:
    def __init__(self):
        self.expectations: dict[str, Expectation] = {}
        self._counter = 0

    def _next_id(self, pair: str) -> str:
        self._counter += 1
        return f"{pair}_eof_{self._counter}"

    def create_expectation(
        self,
        pair: str,
        direction: str,
        poi: POI | None,
        zone: tuple[float, float],
        created_at: datetime | None = None,
    ) -> Expectation:
        """Create a new expectation when a structural extreme forms."""
        exp = Expectation(
            id=self._next_id(pair),
            pair=pair,
            direction=direction,
            anticipated_poi=poi,
            anticipated_price_zone=zone,
            created_at=created_at or datetime.utcnow(),
        )
        self.expectations[exp.id] = exp
        return exp

    def check_price_arrival(self, exp_id: str, current_price: float, timestamp: datetime) -> bool:
        """Check if price has arrived at the anticipated zone."""
        exp = self.expectations.get(exp_id)
        if not exp or exp.status != ExpectationStatus.PENDING:
            return False

        lo, hi = exp.anticipated_price_zone
        if lo <= current_price <= hi:
            exp.status = ExpectationStatus.PRICE_ARRIVED
            exp.arrived_at = timestamp
            return True
        return False

    def trigger(self, exp_id: str, timestamp: datetime) -> None:
        """Mark an expectation as triggered (entry taken)."""
        exp = self.expectations.get(exp_id)
        if exp and exp.status == ExpectationStatus.PRICE_ARRIVED:
            exp.status = ExpectationStatus.TRIGGERED
            exp.triggered_at = timestamp

    def expire(self, exp_id: str, reason: str) -> None:
        """Expire an expectation (e.g., CHoCH invalidated the premise)."""
        exp = self.expectations.get(exp_id)
        if exp and exp.status in (ExpectationStatus.PENDING, ExpectationStatus.PRICE_ARRIVED):
            exp.status = ExpectationStatus.EXPIRED
            exp.expired_reason = reason

    def get_active(self, pair: str | None = None) -> list[Expectation]:
        """Get all PENDING or PRICE_ARRIVED expectations."""
        active = [e for e in self.expectations.values()
                  if e.status in (ExpectationStatus.PENDING, ExpectationStatus.PRICE_ARRIVED)]
        if pair:
            active = [e for e in active if e.pair == pair]
        return active
