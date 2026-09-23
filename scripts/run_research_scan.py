"""Run the Phase 2 research pipeline: scan sources, score ideas with OpenRouter,
and persist new ideas to the database.

Usage:
    PYTHONPATH=. .venv/Scripts/python scripts/run_research_scan.py [max_results]
"""
from __future__ import annotations

import logging
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from agents.research.scanner import scan_arxiv, scan_ssrn, scan_quantconnect
from agents.research.scorer import process_idea
from db import SessionLocal
from db.models import StrategyIdea as StrategyIdeaORM

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    max_results = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    ideas = scan_arxiv(max_results=max_results)
    for scanner in (scan_ssrn, scan_quantconnect):
        try:
            ideas.extend(scanner())
        except Exception:
            logger.exception("%s failed, continuing", scanner.__name__)

    if not ideas:
        logger.warning("No ideas found from any source.")
        return

    db = SessionLocal()
    saved = 0
    try:
        for idea in ideas:
            existing = (
                db.query(StrategyIdeaORM)
                .filter(StrategyIdeaORM.source_url == idea.source_url)
                .first()
            )
            if existing:
                logger.info("Skipping already-seen idea: %s", idea.title)
                continue

            if idea.abstract:
                process_idea(idea)
                time.sleep(5)

            db.add(
                StrategyIdeaORM(
                    title=idea.title,
                    source_url=idea.source_url,
                    source_type=idea.source_type,
                    abstract=idea.abstract,
                    hypothesis=idea.hypothesis,
                    methodology=idea.methodology,
                    asset_class=idea.asset_class,
                    edge_claim=idea.edge_claim,
                    red_flags=idea.red_flags,
                    score_sharpe_potential=idea.score_sharpe_potential,
                    score_data_availability=idea.score_data_availability,
                    score_complexity=idea.score_complexity,
                    score_capital_requirement=idea.score_capital_requirement,
                    score_time_horizon=idea.score_time_horizon,
                    total_score=idea.total_score,
                    nim_summary=idea.nim_summary,
                )
            )
            saved += 1
            logger.info(
                "Saved idea: %s (score=%s, red_flags=%s)",
                idea.title,
                idea.total_score,
                idea.red_flags,
            )

        db.commit()
    finally:
        db.close()

    logger.info("Done. %d new ideas saved out of %d scanned.", saved, len(ideas))


if __name__ == "__main__":
    main()
