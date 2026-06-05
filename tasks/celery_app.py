"""Celery application factory with Redis as broker and result backend."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from config import settings

celery_app = Celery(
    "quant_os",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "tasks.data_tasks",
        "tasks.crt_tasks",
        "tasks.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    # Refresh MT5 data every minute during trading hours
    "crt-scan-every-minute": {
        "task": "tasks.crt_tasks.run_crt_scan",
        "schedule": settings.crt_scan_interval_seconds,
    },
    # Weekly performance report every Sunday at 18:00 UTC
    "weekly-report-sunday": {
        "task": "tasks.report_tasks.generate_weekly_report",
        "schedule": crontab(hour=18, minute=0, day_of_week="sunday"),
    },
}
