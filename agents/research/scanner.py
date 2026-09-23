"""Scanners that pull candidate strategy ideas from public sources.

Each scanner returns a list of `StrategyIdea` with at least
title / source_url / source_type / abstract populated.
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import requests

from agents.research.models import StrategyIdea

logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def scan_arxiv(query: str = "cat:q-fin.TR", max_results: int = 10) -> list[StrategyIdea]:
    """Scan arXiv's Quantitative Finance categories for recent papers."""
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    resp = requests.get(ARXIV_API_URL, params=params, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    ideas: list[StrategyIdea] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title_el = entry.find("atom:title", ATOM_NS)
        summary_el = entry.find("atom:summary", ATOM_NS)
        id_el = entry.find("atom:id", ATOM_NS)
        if title_el is None or id_el is None:
            continue

        title = " ".join(title_el.text.split()) if title_el.text else "Untitled"
        abstract = " ".join(summary_el.text.split()) if summary_el is not None and summary_el.text else None

        ideas.append(
            StrategyIdea(
                title=title,
                source_url=id_el.text,
                source_type="arxiv",
                abstract=abstract,
            )
        )

    logger.info("scan_arxiv: found %d papers for query=%r", len(ideas), query)
    return ideas


def scan_ssrn(query: str = "trading strategy", max_results: int = 10) -> list[StrategyIdea]:
    """Best-effort scan of SSRN search results.

    SSRN aggressively blocks scraping/JS-rendered content, so this may
    return an empty list in restricted environments. Failures are logged
    and swallowed rather than raised, since this scanner is supplementary.
    """
    url = "https://papers.ssrn.com/sol3/results.cfm"
    try:
        resp = requests.get(url, params={"term": query}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("scan_ssrn: request failed (%s) — returning no results", exc)
        return []

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(resp.text, "html.parser")
    ideas: list[StrategyIdea] = []
    for link in soup.select("a.title, a[href*='abstract']")[:max_results]:
        title = link.get_text(strip=True)
        href = link.get("href")
        if not title or not href:
            continue
        if not href.startswith("http"):
            href = f"https://papers.ssrn.com{href}"
        ideas.append(StrategyIdea(title=title, source_url=href, source_type="ssrn"))

    logger.info("scan_ssrn: found %d results for query=%r", len(ideas), query)
    return ideas


def scan_quantconnect(max_results: int = 10) -> list[StrategyIdea]:
    """Best-effort scan of the QuantConnect community forum for strategy threads."""
    url = "https://www.quantconnect.com/forum/discussions"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("scan_quantconnect: request failed (%s) — returning no results", exc)
        return []

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(resp.text, "html.parser")
    ideas: list[StrategyIdea] = []
    for link in soup.select("a.forum-discussion-link, a[href*='/forum/discussion/']")[:max_results]:
        title = link.get_text(strip=True)
        href = link.get("href")
        if not title or not href:
            continue
        if not href.startswith("http"):
            href = f"https://www.quantconnect.com{href}"
        ideas.append(StrategyIdea(title=title, source_url=href, source_type="quantconnect"))

    logger.info("scan_quantconnect: found %d results", len(ideas))
    return ideas


def scan_all() -> list[StrategyIdea]:
    """Run all scanners and return the combined list of ideas."""
    ideas: list[StrategyIdea] = []
    for scanner in (scan_arxiv, scan_ssrn, scan_quantconnect):
        try:
            ideas.extend(scanner())
        except Exception:
            logger.exception("%s failed", scanner.__name__)
    return ideas
