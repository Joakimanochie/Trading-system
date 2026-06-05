"""CRT Agent main loop — stub (Phase 4 implementation)."""
from __future__ import annotations

import logging

logger = logging.getLogger("quant_os.agents.crt.runner")


def scan_all_pairs() -> list[dict]:
    """
    Iterate all CRT_PAIRS and run the full CRT pipeline for each.
    Returns list of scan result dicts (one per pair).
    Stub — full implementation in Phase 4.
    """
    from config import settings

    results = []
    for pair in settings.crt_pairs_list:
        logger.debug(f"Scanning {pair} (stub)")
        results.append({"pair": pair, "status": "stub"})
    return results
