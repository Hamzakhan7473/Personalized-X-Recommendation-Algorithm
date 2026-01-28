"""Home Mixer: orchestration layer for the For You feed pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from schemas import AlgorithmPreferences, FeedItem, FeedResponse, PostWithAuthor

if TYPE_CHECKING:
    from store import Store

from .filters import apply_pre_scoring_filters
from .scorers import author_diversity_scorer, weighted_scorer
from .sources import get_candidates
from .types import Candidate, ScoredCandidate

if TYPE_CHECKING:
    from store import Store


class HomeMixer:
    """
    Orchestrates Query Hydration → Sources → Hydration → Filters → Scorers → Selection.
    Uses the store for Thunder-style in-network and Phoenix-style OON candidates.
    """

    def __init__(self, store: "Store"):
        self.store = store

    def get_feed(
        self,
        user_id: str,
        preferences: AlgorithmPreferences | None = None,
        limit: int = 50,
        seen_post_ids: set[str] | None = None,
        include_explanations: bool = True,
    ) -> FeedResponse:
        """Run the full pipeline and return a ranked feed with optional explanations."""
        prefs = preferences or AlgorithmPreferences()
        seen = seen_post_ids or set()

        # 1) Candidate sourcing (Thunder + Phoenix-style)
        candidates = get_candidates(
            self.store,
            user_id,
            friends_vs_global=prefs.friends_vs_global,
            limits=(200, 150),
        )

        # 2) Pre-scoring filters
        filtered = apply_pre_scoring_filters(
            candidates,
            viewer_id=user_id,
            store=self.store,
            max_age_hours=168,
            seen_post_ids=seen,
        )

        # 3) Weighted scoring + explainability
        scored = weighted_scorer(filtered, prefs)

        # 4) Author diversity re-scoring
        scored = author_diversity_scorer(scored, prefs)

        # 5) Selection: top K
        top = sorted(scored, key=lambda s: s.final_score, reverse=True)[:limit]

        # 6) Build feed items (hydrate author + engagement counts on post)
        items: list[FeedItem] = []
        for s in top:
            post = s.candidate.post
            author = s.candidate.author
            counts = s.candidate.engagement_counts
            data = post.model_dump()
            data["like_count"] = counts.get("like", 0)
            data["repost_count"] = counts.get("repost", 0)
            data["reply_count"] = counts.get("reply", 0)
            data["quote_count"] = counts.get("quote", 0)
            post_with_author = PostWithAuthor(**data, author=author)
            items.append(
                FeedItem(
                    post=post_with_author,
                    ranking_explanation=s.explanation if include_explanations else None,
                )
            )

        return FeedResponse(items=items, next_cursor=None)
