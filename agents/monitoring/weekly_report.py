"""Weekly performance report — auto-generated every Sunday via Celery Beat."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from agents.monitoring.alerts import send_telegram, send_email

logger = logging.getLogger(__name__)


@dataclass
class WeeklyReport:
    period_start: datetime
    period_end: datetime
    total_pnl: float
    total_trades: int
    win_rate: float
    best_trade: dict = field(default_factory=dict)
    worst_trade: dict = field(default_factory=dict)
    per_strategy: list[dict] = field(default_factory=list)
    crt_hit_rate: float = 0.0
    photon_hit_rate: float = 0.0
    regime_notes: list[str] = field(default_factory=list)


def build_weekly_report() -> WeeklyReport:
    """Build the weekly performance summary from DB data."""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    try:
        from db import SessionLocal
        from db.models import Trade, PerformanceRecord
        db = SessionLocal()

        trades = db.query(Trade).filter(Trade.created_at >= week_ago).all()
        total_pnl = sum(float(t.realized_pnl or 0) for t in trades)
        total_trades = len(trades)
        wins = sum(1 for t in trades if float(t.realized_pnl or 0) > 0)
        win_rate = wins / total_trades if total_trades > 0 else 0.0

        best = max(trades, key=lambda t: float(t.realized_pnl or 0), default=None)
        worst = min(trades, key=lambda t: float(t.realized_pnl or 0), default=None)

        db.close()

        return WeeklyReport(
            period_start=week_ago,
            period_end=now,
            total_pnl=round(total_pnl, 2),
            total_trades=total_trades,
            win_rate=round(win_rate, 4),
            best_trade={"pnl": float(best.realized_pnl)} if best else {},
            worst_trade={"pnl": float(worst.realized_pnl)} if worst else {},
        )
    except Exception as e:
        logger.error("Failed to build weekly report: %s", e)
        return WeeklyReport(
            period_start=week_ago, period_end=now,
            total_pnl=0, total_trades=0, win_rate=0,
        )


def format_report(report: WeeklyReport) -> str:
    """Format the weekly report as text."""
    lines = [
        f"📊 <b>Weekly Report</b> ({report.period_start.strftime('%b %d')} - {report.period_end.strftime('%b %d')})",
        f"Total P&L: ${report.total_pnl:,.2f}",
        f"Trades: {report.total_trades} | Win rate: {report.win_rate*100:.0f}%",
    ]
    if report.best_trade:
        lines.append(f"Best: ${report.best_trade.get('pnl', 0):,.2f}")
    if report.worst_trade:
        lines.append(f"Worst: ${report.worst_trade.get('pnl', 0):,.2f}")
    if report.per_strategy:
        lines.append("\nPer strategy:")
        for s in report.per_strategy:
            lines.append(f"  {s.get('name', '?')}: ${s.get('pnl', 0):,.2f}")
    if report.regime_notes:
        lines.append(f"\nRegime: {'; '.join(report.regime_notes)}")
    return "\n".join(lines)


def build_and_send_weekly_report() -> None:
    """Build the weekly report and dispatch via Telegram/email."""
    report = build_weekly_report()
    text = format_report(report)
    logger.info("Weekly report:\n%s", text)
    send_telegram(text)
    send_email("Weekly Report", text)
