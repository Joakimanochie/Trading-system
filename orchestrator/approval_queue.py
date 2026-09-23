"""Redis-backed approval queue for pending human decisions."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

from config import settings
from orchestrator.audit_log import write_audit_log

logger = logging.getLogger(__name__)

QUEUE_KEY = "quant_os:approval_queue"


def _get_redis():
    import redis
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


@dataclass
class PendingApproval:
    signal_id: str
    source_agent: str
    pair: str
    direction: str
    entry_price: float
    sl: float
    tp1: float
    position_size: float
    created_at: str
    expires_at: str


def push_to_queue(
    signal_id: str,
    source_agent: str,
    pair: str,
    direction: str,
    entry_price: float,
    sl: float,
    tp1: float,
    position_size: float,
    timeout_mins: int | None = None,
) -> PendingApproval:
    """Push a signal to the approval queue."""
    if timeout_mins is None:
        timeout_mins = settings.signal_approval_timeout_mins

    now = datetime.utcnow()
    expires = now + timedelta(minutes=timeout_mins)

    item = PendingApproval(
        signal_id=signal_id,
        source_agent=source_agent,
        pair=pair,
        direction=direction,
        entry_price=entry_price,
        sl=sl,
        tp1=tp1,
        position_size=position_size,
        created_at=now.isoformat(),
        expires_at=expires.isoformat(),
    )

    r = _get_redis()
    r.hset(QUEUE_KEY, signal_id, json.dumps(item.__dict__))
    logger.info("Approval queued: %s %s %s (expires %s)", signal_id, pair, direction, expires)
    return item


def get_pending() -> list[PendingApproval]:
    """Get all pending approvals, removing expired ones."""
    r = _get_redis()
    all_items = r.hgetall(QUEUE_KEY)
    now = datetime.utcnow()
    pending = []

    for signal_id, data_str in all_items.items():
        data = json.loads(data_str)
        expires = datetime.fromisoformat(data["expires_at"])

        if now > expires:
            r.hdel(QUEUE_KEY, signal_id)
            logger.info("Signal %s expired, auto-rejected", signal_id)
            write_audit_log(
                actor="approval_queue",
                action="signal_expired",
                details={"signal_id": signal_id},
                outcome="expired",
            )
            continue

        pending.append(PendingApproval(**data))

    return pending


def approve(signal_id: str, actor: str = "human") -> bool:
    """Approve a pending signal."""
    r = _get_redis()
    data = r.hget(QUEUE_KEY, signal_id)
    if not data:
        return False

    r.hdel(QUEUE_KEY, signal_id)
    write_audit_log(actor=actor, action="signal_approved", details={"signal_id": signal_id}, outcome="approved")
    logger.info("Signal %s APPROVED by %s", signal_id, actor)
    return True


def reject(signal_id: str, actor: str = "human", reason: str = "") -> bool:
    """Reject a pending signal."""
    r = _get_redis()
    data = r.hget(QUEUE_KEY, signal_id)
    if not data:
        return False

    r.hdel(QUEUE_KEY, signal_id)
    write_audit_log(actor=actor, action="signal_rejected", details={"signal_id": signal_id, "reason": reason}, outcome="rejected")
    logger.info("Signal %s REJECTED by %s: %s", signal_id, actor, reason)
    return True
