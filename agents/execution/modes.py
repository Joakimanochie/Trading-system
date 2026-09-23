"""Execution modes: AUTO and MANUAL with signal expiry logic."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum

from config import settings

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"


def get_current_mode() -> ExecutionMode:
    return ExecutionMode(settings.execution_mode)


def is_signal_expired(signal_created_at: datetime) -> bool:
    """Check if an unapproved signal has expired past the timeout."""
    timeout = timedelta(minutes=settings.signal_approval_timeout_mins)
    expired = datetime.utcnow() - signal_created_at > timeout
    if expired:
        logger.info("Signal from %s expired (timeout=%d min)", signal_created_at, settings.signal_approval_timeout_mins)
    return expired


def should_auto_execute(signal_created_at: datetime) -> bool:
    """Returns True only if in AUTO mode and signal is not expired."""
    if get_current_mode() != ExecutionMode.AUTO:
        return False
    if is_signal_expired(signal_created_at):
        return False
    return True
