"""Celery tasks for the CRT Agent."""
from __future__ import annotations

import logging

from tasks.celery_app import celery_app

logger = logging.getLogger("quant_os.agents.crt")


@celery_app.task(name="tasks.crt_tasks.run_crt_scan", bind=True)
def run_crt_scan(self):
    """Trigger CRT scan across all configured pairs."""
    try:
        from agents.crt.runner import scan_all_pairs

        results = scan_all_pairs()
        logger.info(f"CRT scan complete — {len(results)} pairs processed")
        return {"pairs_scanned": len(results)}
    except Exception as exc:
        logger.error(f"CRT scan failed: {exc}")
        return {"error": str(exc)}
