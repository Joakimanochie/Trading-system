"""Quick Phase 8 verification script."""
from dotenv import load_dotenv
load_dotenv()

from orchestrator.state_machine import VALID_TRANSITIONS
from orchestrator.signal_router import route_signal
from orchestrator.approval_queue import push_to_queue, get_pending, approve
from orchestrator.health_monitor import record_heartbeat, check_system_health
from orchestrator.audit_log import write_audit_log
print("All modules loaded OK")

routed = route_signal("test-001", "crt_agent", "EURUSD", "LONG", 1.082, 1.080, 1.086,
                       capital=100000, win_rate=0.56, profit_factor=7.63)
print("Routed to:", routed.routed_to, "size=", round(routed.position_size, 2))

rejected = route_signal("test-002", "crt_agent", "GBPUSD", "SHORT", 1.264, 1.266, 1.260,
                          current_drawdown=0.20)
print("Rejected:", rejected.routed_to, "violations=", rejected.risk_violations)

item = push_to_queue("test-001", "crt_agent", "EURUSD", "LONG", 1.082, 1.080, 1.086, 50000.0)
print("Queued:", item.signal_id, "pending=", len(get_pending()))
approve("test-001", "human:tobe")
print("After approve: pending=", len(get_pending()))

record_heartbeat("crt_agent")
record_heartbeat("risk_agent")
health = check_system_health(["crt_agent", "risk_agent", "photon_agent"])
print("Health: overall=", health.overall_healthy, "redis=", health.redis_connected, "db=", health.db_connected)

from db.models import StrategyStatus
print("BACKTESTING ->", [s.value for s in VALID_TRANSITIONS[StrategyStatus.BACKTESTING]])
print("Phase 8 verified.")
