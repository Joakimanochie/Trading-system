"""Immutable append-only audit log writer."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("quant_os.orchestrator.audit")


def write_audit_log(
    actor: str,
    action: str,
    details: dict[str, Any] | None = None,
    strategy_id: str | None = None,
    outcome: str | None = None,
) -> None:
    """Append one entry to the audit log in the database."""
    from db import SessionLocal
    from db.models import AuditLog

    entry = AuditLog(
        timestamp=datetime.now(timezone.utc),
        actor=actor,
        action=action,
        strategy_id=strategy_id,
        details=details,
        outcome=outcome,
    )

    with SessionLocal() as db:
        db.add(entry)
        db.commit()

    logger.info(f"AUDIT | {actor} | {action} | outcome={outcome}")
