"""Celery tasks for report generation."""
from __future__ import annotations

import logging

from tasks.celery_app import celery_app

logger = logging.getLogger("quant_os.tasks.reports")


@celery_app.task(name="tasks.report_tasks.generate_weekly_report")
def generate_weekly_report():
    """Generate and dispatch the Sunday weekly performance report."""
    try:
        from agents.monitoring.weekly_report import build_and_send_weekly_report

        build_and_send_weekly_report()
        logger.info("Weekly report generated and dispatched")
        return {"status": "sent"}
    except Exception as exc:
        logger.error(f"Weekly report failed: {exc}")
        return {"error": str(exc)}
