"""MT5 terminal watchdog: health check, auto-restart, alert + PAUSE after 3 failures."""
from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MT5_TERMINAL_PATH = r"C:\Users\Hp\AppData\Roaming\MetaTrader 5\terminal64.exe"


@dataclass
class WatchdogState:
    healthy: bool = True
    consecutive_failures: int = 0
    max_failures: int = 3
    last_check: float = 0.0
    paused: bool = False


def check_mt5_health() -> bool:
    """Check if MT5 terminal is running and responsive."""
    try:
        import MetaTrader5 as mt5
        info = mt5.terminal_info()
        return info is not None
    except Exception:
        return False


def restart_mt5_terminal(terminal_path: str = MT5_TERMINAL_PATH) -> bool:
    """Kill and relaunch the MT5 terminal."""
    try:
        subprocess.run(["taskkill", "/F", "/IM", "terminal64.exe"], capture_output=True)
        time.sleep(2)
        subprocess.Popen([terminal_path])
        time.sleep(10)

        import MetaTrader5 as mt5
        from config import settings
        success = mt5.initialize(
            path=terminal_path,
            login=int(settings.mt5_login),
            password=settings.mt5_password,
            server=settings.mt5_server,
        )
        if success:
            logger.info("MT5 terminal restarted successfully")
        return success
    except Exception as e:
        logger.error("MT5 restart failed: %s", e)
        return False


def pause_crt_agent(reason: str) -> None:
    """Set CRT agent status to PAUSED in the DB."""
    try:
        from db import SessionLocal
        from db.models import Strategy, StrategyStatus
        db = SessionLocal()
        strats = db.query(Strategy).filter(Strategy.name.like("%crt%")).all()
        for s in strats:
            s.status = StrategyStatus.PAUSED
        db.commit()
        db.close()
        logger.critical("CRT Agent PAUSED: %s", reason)
    except Exception as e:
        logger.error("Failed to pause CRT agent: %s", e)


def run_watchdog_check(state: WatchdogState) -> WatchdogState:
    """Single watchdog iteration. Call this every 60s."""
    if state.paused:
        return state

    healthy = check_mt5_health()
    state.last_check = time.time()

    if healthy:
        state.healthy = True
        state.consecutive_failures = 0
        return state

    state.healthy = False
    state.consecutive_failures += 1
    logger.warning("MT5 health check failed (%d/%d)", state.consecutive_failures, state.max_failures)

    if state.consecutive_failures < state.max_failures:
        logger.info("Attempting MT5 restart...")
        if restart_mt5_terminal():
            state.consecutive_failures = 0
            state.healthy = True
    else:
        state.paused = True
        pause_crt_agent(f"MT5 watchdog: {state.max_failures} consecutive failures")

    return state
