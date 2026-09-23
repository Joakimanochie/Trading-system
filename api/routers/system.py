"""System endpoints: health, kill switch, audit log, approval queue."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from db import get_db
from db.models import AuditLog

router = APIRouter()


@router.get("/health")
def system_health():
    from orchestrator.health_monitor import check_system_health
    health = check_system_health()
    return {
        "status": "ok" if health.overall_healthy else "degraded",
        "redis": health.redis_connected,
        "db": health.db_connected,
        "mt5": health.mt5_connected,
        "agents": [{"name": a.name, "healthy": a.healthy, "details": a.details} for a in health.agents],
    }


@router.post("/kill")
def kill_switch(confirm: str = "", flatten: bool = True):
    if confirm != "CONFIRM_KILL":
        raise HTTPException(status_code=400, detail="Must pass confirm=CONFIRM_KILL to activate kill switch")
    from agents.execution.kill_switch import activate_kill_switch
    result = activate_kill_switch(flatten=flatten)
    return {
        "status": "kill_switch_activated",
        "orders_cancelled": result.orders_cancelled,
        "positions_closed": result.positions_closed,
        "errors": result.errors,
    }


@router.get("/audit")
def get_audit_log(
    agent: str | None = None,
    strategy: str | None = None,
    limit: int = Query(default=50, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if agent:
        q = q.filter(AuditLog.actor.contains(agent))
    if strategy:
        q = q.filter(AuditLog.strategy_id == strategy)
    return q.limit(limit).all()


@router.get("/approvals")
def get_pending_approvals():
    from orchestrator.approval_queue import get_pending
    return [a.__dict__ for a in get_pending()]


@router.post("/approvals/{signal_id}/approve")
def approve_signal(signal_id: str):
    from orchestrator.approval_queue import approve
    if approve(signal_id):
        return {"status": "approved", "signal_id": signal_id}
    raise HTTPException(status_code=404, detail="Signal not found in queue")


@router.post("/approvals/{signal_id}/reject")
def reject_signal(signal_id: str, reason: str = ""):
    from orchestrator.approval_queue import reject
    if reject(signal_id, reason=reason):
        return {"status": "rejected", "signal_id": signal_id}
    raise HTTPException(status_code=404, detail="Signal not found in queue")
