"""OpenRouter owl-alpha powered extraction and scoring of strategy ideas.

Uses the shared `nim_complete` client only — no separate LLM SDK.
"""
from __future__ import annotations

import json
import logging
import re
import time

from agents.shared.nim_client import nim_complete
from agents.research.models import StrategyIdea

logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _parse_json(text: str) -> dict:
    """Extract a JSON object from an LLM response, tolerating markdown fences."""
    match = _JSON_FENCE_RE.search(text)
    candidate = match.group(1) if match else text
    return json.loads(candidate)


def extract_idea_info(idea: StrategyIdea) -> StrategyIdea:
    """Use owl-alpha to extract hypothesis, methodology, asset class and edge claim
    from the paper's abstract, plus a short human-readable summary."""
    if not idea.abstract:
        logger.warning("extract_idea_info: idea %r has no abstract, skipping", idea.title)
        return idea

    system = (
        "You are a quantitative research analyst. Given a paper's title and abstract, "
        "extract structured information. Respond with ONLY a JSON object with keys: "
        "hypothesis (string), methodology (string), asset_class (string), "
        "edge_claim (string), summary (string, 2-3 sentences)."
    )
    prompt = f"Title: {idea.title}\n\nAbstract: {idea.abstract}"

    response = nim_complete(prompt, system=system, temperature=0.3)
    try:
        data = _parse_json(response)
    except (json.JSONDecodeError, AttributeError):
        logger.warning("extract_idea_info: failed to parse JSON for %r: %s", idea.title, response)
        return idea

    idea.hypothesis = data.get("hypothesis")
    idea.methodology = data.get("methodology")
    idea.asset_class = data.get("asset_class")
    idea.edge_claim = data.get("edge_claim")
    idea.nim_summary = data.get("summary")
    return idea


def score_idea(idea: StrategyIdea) -> StrategyIdea:
    """Use owl-alpha to score the idea on the standard rubric (0-10 each)."""
    system = (
        "You are a quantitative research analyst scoring strategy ideas on a 0-10 scale "
        "(0 = worst/lowest, 10 = best/highest) along five dimensions:\n"
        "- sharpe_potential: likelihood the strategy achieves a strong risk-adjusted return\n"
        "- data_availability: how easy it is to obtain the data needed (10 = freely available)\n"
        "- complexity: implementation simplicity (10 = very simple to implement)\n"
        "- capital_requirement: how little capital is needed to trade this (10 = very low capital)\n"
        "- time_horizon: how suitable the horizon is for a retail trader (10 = ideal horizon)\n"
        "Respond with ONLY a JSON object with keys: sharpe_potential, data_availability, "
        "complexity, capital_requirement, time_horizon (all numbers 0-10)."
    )
    prompt = (
        f"Title: {idea.title}\n"
        f"Hypothesis: {idea.hypothesis}\n"
        f"Methodology: {idea.methodology}\n"
        f"Asset class: {idea.asset_class}\n"
        f"Edge claim: {idea.edge_claim}"
    )

    response = nim_complete(prompt, system=system, temperature=0.3)
    try:
        data = _parse_json(response)
    except (json.JSONDecodeError, AttributeError):
        logger.warning("score_idea: failed to parse JSON for %r: %s", idea.title, response)
        return idea

    idea.score_sharpe_potential = data.get("sharpe_potential")
    idea.score_data_availability = data.get("data_availability")
    idea.score_complexity = data.get("complexity")
    idea.score_capital_requirement = data.get("capital_requirement")
    idea.score_time_horizon = data.get("time_horizon")
    idea.compute_total_score()
    return idea


def flag_red_flags(idea: StrategyIdea) -> StrategyIdea:
    """Use owl-alpha to flag common red flags: missing economic rationale,
    implausible Sharpe claims, data mining indicators, etc."""
    system = (
        "You are a skeptical quantitative researcher reviewing a strategy idea for red flags. "
        "Check for: lack of economic rationale, implausibly high Sharpe ratio or return claims, "
        "signs of data mining / overfitting (e.g. many parameters, short backtest window, "
        "curve-fit-sounding language), and reliance on data that is hard to obtain or survivorship-biased. "
        "Respond with ONLY a JSON object with key 'red_flags': a list of short strings "
        "(empty list if none found)."
    )
    prompt = (
        f"Title: {idea.title}\n"
        f"Hypothesis: {idea.hypothesis}\n"
        f"Methodology: {idea.methodology}\n"
        f"Edge claim: {idea.edge_claim}\n"
        f"Abstract: {idea.abstract}"
    )

    response = nim_complete(prompt, system=system, temperature=0.3)
    try:
        data = _parse_json(response)
    except (json.JSONDecodeError, AttributeError):
        logger.warning("flag_red_flags: failed to parse JSON for %r: %s", idea.title, response)
        return idea

    idea.red_flags = data.get("red_flags", [])
    return idea


def process_idea(idea: StrategyIdea, delay: float = 3.0) -> StrategyIdea:
    """Run the full LLM pipeline on a single idea: extract, score, flag red flags.

    A small delay between calls avoids tripping the API's rate limit.
    """
    extract_idea_info(idea)
    time.sleep(delay)
    score_idea(idea)
    time.sleep(delay)
    flag_red_flags(idea)
    return idea
