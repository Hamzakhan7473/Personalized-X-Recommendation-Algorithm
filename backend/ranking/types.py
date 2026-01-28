"""Internal types for the ranking pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from schemas import AlgorithmPreferences, Post, PostWithAuthor, RankingExplanation, User


@dataclass
class Candidate:
    """Enriched candidate post with metadata for scoring."""
    post: Post
    author: User | None = None
    source: str = "in_network"  # "in_network" | "out_of_network"
    engagement_counts: dict[str, int] = field(default_factory=dict)
    # Placeholder for ML action probabilities; we use heuristic-derived scores
    action_scores: dict[str, float] = field(default_factory=dict)
    raw_features: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredCandidate:
    """Candidate plus final score and explainability."""
    candidate: Candidate
    final_score: float
    explanation: RankingExplanation
