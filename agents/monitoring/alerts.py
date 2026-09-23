"""Alert dispatcher: Telegram + email for all system events."""
from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from enum import Enum

import requests

from config import settings

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    DRAWDOWN_WARNING = "drawdown_warning"
    DAILY_LOSS_BREACH = "daily_loss_breach"
    STRATEGY_PAUSED = "strategy_paused"
    REGIME_SHIFT = "regime_shift"
    DATA_STALE = "data_stale"
    BROKER_DISCONNECT = "broker_disconnect"
    MT5_FEED_STALE = "mt5_feed_stale"
    SIGNAL_GENERATED = "signal_generated"
    KILL_SWITCH = "kill_switch"


def send_telegram(message: str) -> bool:
    """Send alert via Telegram bot."""
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id
    if not token or not chat_id:
        logger.debug("Telegram not configured, skipping")
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return False


def send_email(subject: str, body: str) -> bool:
    """Send alert via email."""
    if not settings.email_username or not settings.email_alert_recipient:
        logger.debug("Email not configured, skipping")
        return False

    try:
        msg = MIMEText(body)
        msg["Subject"] = f"[Quant OS] {subject}"
        msg["From"] = settings.email_username
        msg["To"] = settings.email_alert_recipient

        with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port) as server:
            server.starttls()
            server.login(settings.email_username, settings.email_password)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error("Email send failed: %s", e)
        return False


def dispatch_alert(alert_type: AlertType, message: str, critical: bool = False) -> None:
    """Send alert through all configured channels."""
    prefix = "🚨 CRITICAL" if critical else "⚠️ Alert"
    full_message = f"{prefix} [{alert_type.value}]\n{message}"

    logger.warning("ALERT [%s]: %s", alert_type.value, message)
    send_telegram(full_message)

    if critical:
        send_email(f"{alert_type.value}", message)
