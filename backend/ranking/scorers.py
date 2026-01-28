"""Weighted scorer and author-diversity scorer. Preference-driven and explainable."""

from __future__ import annotations

import math
import time
from collections import defaultdict

from schemas import ActionScore, AlgorithmPreferences, RankingExplanation

from .types import Candidate, ScoredCandidate


# Action keys aligned with X-style multi-action prediction
ACTIONS_POSITIVE = ["like", "repost", "reply", "quote", "click", "share", "follow_author"]
ACTIONS_NEGATIVE = ["not_interested", "block_author", "mute_author", "report"]


def _heuristic_action_scores(c: Candidate, prefs: AlgorithmPreferences) -> dict[str, float]:
    """Heuristic 'probabilities' for each action (no real ML model). Used for tunable scoring."""
    likes = c.engagement_counts.get("like", 0)
    reposts = c.engagement_counts.get("repost", 0)
    replies = c.engagement_counts.get("reply", 0)
    age_seconds = time.time() - c.post.created_at
    recency_score = 1.0 / (1.0 + age_seconds / 3600)  # decay over hours

    # Popularity score (bounded)
    pop = (likes * 1.0 + reposts * 2.0 + replies * 1.5)
    pop_score = min(1.0, math.tanh(pop / 10) * 0.5 + 0.5)

    # Recency vs popularity blend
    rv = prefs.recency_vs_popularity
    base_positive = (1 - rv) * recency_score + rv * pop_score

    out: dict[str, float] = {}
    out["like"] = base_positive * (0.4 + 0.3 * min(1, likes / 20))
    out["repost"] = base_positive * (0.2 + 0.2 * min(1, reposts / 10))
    out["reply"] = base_positive * 0.25
    out["quote"] = base_positive * 0.15
    out["click"] = base_positive * 0.5
    out["share"] = base_positive * 0.2
    out["follow_author"] = base_positive * 0.1
    out["not_interested"] = 0.05 * prefs.negative_signal_strength
    out["block_author"] = 0.02 * prefs.negative_signal_strength
    out["mute_author"] = 0.03 * prefs.negative_signal_strength
    out["report"] = 0.01 * prefs.negative_signal_strength
    return out


def _topic_boost(post_topics: list[str], prefs: AlgorithmPreferences) -> float:
    """Boost from topic weights (tech, politics, culture, memes, finance)."""
    w = {
        "tech": prefs.tech_weight,
        "politics": prefs.politics_weight,
        "culture": prefs.culture_weight,
        "memes": prefs.memes_weight,
        "finance": prefs.finance_weight,
    }
    if not post_topics:
        return 0.5  # neutral
    return sum(w.get(t, 0.1) for t in post_topics) / max(1, len(post_topics))


def _recency_boost(created_at: float) -> float:
    """Pure recency component for explanation."""
    age = time.time() - created_at
    return 1.0 / (1.0 + age / 3600)


def weighted_scorer(candidates: list[Candidate], prefs: AlgorithmPreferences) -> list[ScoredCandidate]:
    """
    Score each candidate: weighted sum of action 'probabilities' plus topic/recency.
    Produces RankingExplanation per candidate.
    """
    # Weights for positive actions (tunable via prefs could be extended)
    pos_weights = {"like": 1.0, "repost": 1.2, "reply": 1.0, "quote": 0.8, "click": 0.6, "share": 0.9, "follow_author": 0.7}
    neg_weights = {"not_interested": -1.5, "block_author": -2.0, "mute_author": -1.8, "report": -2.0}

    out: list[ScoredCandidate] = []
    for c in candidates:
        probs = _heuristic_action_scores(c, prefs)
        topic_boost = _topic_boost([t.value for t in c.post.topics], prefs)
        recency_boost = _recency_boost(c.post.created_at)

        weighted = 0.0
        action_scores_list: list[ActionScore] = []
        for action, w in pos_weights.items():
            p = probs.get(action, 0)
            contrib = w * p
            weighted += contrib
            action_scores_list.append(ActionScore(action=action, weight=w, probability=p, contribution=contrib))
        for action, w in neg_weights.items():
            p = probs.get(action, 0)
            contrib = w * p
            weighted += contrib
            action_scores_list.append(ActionScore(action=action, weight=w, probability=p, contribution=contrib))

        # In-network boost (when friends_vs_global is low, boost in-network)
        in_net_boost = 1.0 + (1.0 - prefs.friends_vs_global) * 0.5 if c.source == "in_network" else 1.0
        weighted *= in_net_boost

        # Topic and recency blend
        weighted += 0.2 * (topic_boost - 0.5) + 0.1 * (recency_boost - 0.5)

        expl = RankingExplanation(
            post_id=c.post.id,
            final_score=weighted,
            rank=0,
            source=c.source,
            action_scores=action_scores_list,
            diversity_penalty=0.0,
            recency_boost=recency_boost,
            topic_boost=topic_boost,
            raw_breakdown={"in_network_boost": in_net_boost, "probs": probs},
        )
        out.append(ScoredCandidate(candidate=c, final_score=weighted, explanation=expl))
    return out


def author_diversity_scorer(
    scored: list[ScoredCandidate], prefs: AlgorithmPreferences
) -> list[ScoredCandidate]:
    """Attenuate repeated author scores to ensure feed diversity."""
    strength = prefs.diversity_strength
    author_counts: dict[str, int] = defaultdict(int)
    # First pass: assign tentative order by score
    by_score = sorted(scored, key=lambda s: s.final_score, reverse=True)
    new_list: list[ScoredCandidate] = []
    for i, s in enumerate(by_score):
        aid = s.candidate.post.author_id
        author_counts[aid] += 1
        penalty = (author_counts[aid] - 1) * strength * 0.15  # stronger penalty for repeated authors
        new_score = max(0.0, s.final_score - penalty)
        expl = s.explanation.model_copy(update={"final_score": new_score, "rank": i + 1, "diversity_penalty": penalty})
        new_list.append(ScoredCandidate(candidate=s.candidate, final_score=new_score, explanation=expl))
    # Re-sort by new score and fix rank
    by_new = sorted(new_list, key=lambda s: s.final_score, reverse=True)
    for r, s in enumerate(by_new, start=1):
        s.explanation.rank = r
    return by_new
