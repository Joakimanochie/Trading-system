"""In-pipeline representation of a strategy idea, before it's persisted to the DB."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

VALID_SOURCE_TYPES = ("arxiv", "ssrn", "quantconnect")


class IdeaStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BACKTESTING = "BACKTESTING"


@dataclass
class StrategyIdea:
    title: str
    source_url: str | None = None
    source_type: str | None = None  # arxiv | ssrn | quantconnect
    abstract: str | None = None
    hypothesis: str | None = None
    methodology: str | None = None
    asset_class: str | None = None
    edge_claim: str | None = None
    red_flags: list[str] = field(default_factory=list)
    score_sharpe_potential: float | None = None
    score_data_availability: float | None = None
    score_complexity: float | None = None
    score_capital_requirement: float | None = None
    score_time_horizon: float | None = None
    total_score: float | None = None
    status: IdeaStatus = IdeaStatus.PROPOSED
    nim_summary: str | None = None

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("title is required")
        if self.source_type is not None and self.source_type not in VALID_SOURCE_TYPES:
            raise ValueError(f"invalid source_type: {self.source_type!r}")

    def compute_total_score(self) -> float | None:
        """Average the five rubric scores. Returns None if any are missing."""
        scores = [
            self.score_sharpe_potential,
            self.score_data_availability,
            self.score_complexity,
            self.score_capital_requirement,
            self.score_time_horizon,
        ]
        if any(s is None for s in scores):
            return None
        self.total_score = sum(scores) / len(scores)  # type: ignore[arg-type]
        return self.total_score
