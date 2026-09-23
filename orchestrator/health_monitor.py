"""Health monitor: agent heartbeats, data feed freshness, broker/MT5 connection status."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class AgentHealth:
    name: str
    last_heartbeat: datetime | None = None
    healthy: bool = False
    details: str = ""


@dataclass
class SystemHealth:
    timestamp: datetime
    agents: list[AgentHealth]
    mt5_connected: bool = False
    broker_connected: bool = False
    redis_connected: bool = False
    db_connected: bool = False
    data_feed_fresh: bool = False
    overall_healthy: bool = False


_heartbeats: dict[str, datetime] = {}


def record_heartbeat(agent_name: str) -> None:
    """Record a heartbeat from an agent."""
    _heartbeats[agent_name] = datetime.utcnow()


def check_agent_health(agent_name: str, timeout_seconds: int = 120) -> AgentHealth:
    """Check if an agent has sent a heartbeat within the timeout."""
    last = _heartbeats.get(agent_name)
    if last is None:
        return AgentHealth(agent_name, None, False, "No heartbeat recorded")

    age = (datetime.utcnow() - last).total_seconds()
    healthy = age < timeout_seconds
    details = f"Last heartbeat {age:.0f}s ago" if healthy else f"Stale: {age:.0f}s since last heartbeat"
    return AgentHealth(agent_name, last, healthy, details)


def check_redis() -> bool:
    try:
        from config import settings
        import redis
        r = redis.Redis.from_url(settings.redis_url)
        return r.ping()
    except Exception:
        return False


def check_db() -> bool:
    try:
        from db import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception:
        return False


def check_mt5() -> bool:
    try:
        import MetaTrader5 as mt5
        info = mt5.terminal_info()
        return info is not None
    except Exception:
        return False


def check_system_health(
    agent_names: list[str] | None = None,
) -> SystemHealth:
    """Run a full system health check."""
    if agent_names is None:
        agent_names = ["crt_agent", "photon_agent", "risk_agent", "execution_agent", "monitoring_agent"]

    agents = [check_agent_health(name) for name in agent_names]
    redis_ok = check_redis()
    db_ok = check_db()
    mt5_ok = check_mt5()

    overall = all(a.healthy for a in agents) and redis_ok and db_ok

    health = SystemHealth(
        timestamp=datetime.utcnow(),
        agents=agents,
        mt5_connected=mt5_ok,
        broker_connected=False,  # checked when Alpaca is live
        redis_connected=redis_ok,
        db_connected=db_ok,
        data_feed_fresh=mt5_ok,
        overall_healthy=overall,
    )

    if not overall:
        unhealthy = [a.name for a in agents if not a.healthy]
        if unhealthy:
            logger.warning("Unhealthy agents: %s", unhealthy)
        if not redis_ok:
            logger.warning("Redis connection failed")
        if not db_ok:
            logger.warning("Database connection failed")

    return health
