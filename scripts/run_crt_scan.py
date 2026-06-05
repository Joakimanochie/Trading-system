"""CLI: run CRT scan across all pairs and print detected signals."""
from __future__ import annotations

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    from agents.crt.runner import scan_all_pairs

    results = scan_all_pairs()
    for r in results:
        print(r)
