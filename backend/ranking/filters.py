"""Pre-scoring and post-selection filters."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from .types import Candidate

if TYPE_CHECKING:
    from store import Store


def drop_duplicates(candidates: list[Candidate]) -> list[Candidate]:
    """Remove duplicate post IDs (keep first occurrence)."""
    seen: set[str] = set()
    out: list[Candidate] = []
    for c in candidates:
        if c.post.id not in seen:
            seen.add(c.post.id)
            out.append(c)
    return out


def age_filter(candidates: list[Candidate], max_age_hours: float = 168) -> list[Candidate]:
    """Drop posts older than max_age_hours (default 7 days)."""
    cutoff = time.time() - max_age_hours * 3600
    return [c for c in candidates if c.post.created_at >= cutoff]


def self_post_filter(candidates: list[Candidate], viewer_id: str) -> list[Candidate]:
    """Remove viewer's own posts."""
    return [c for c in candidates if c.post.author_id != viewer_id]


def previously_seen_filter(
    candidates: list[Candidate], seen_post_ids: set[str]
) -> list[Candidate]:
    """Remove posts the user has already seen (e.g. from session)."""
    if not seen_post_ids:
        return candidates
    return [c for c in candidates if c.post.id not in seen_post_ids]


def apply_pre_scoring_filters(
    candidates: list[Candidate],
    viewer_id: str,
    store: "Store | None" = None,
    max_age_hours: float = 168,
    seen_post_ids: set[str] | None = None,
) -> list[Candidate]:
    """Run standard pre-scoring filters."""
    out = drop_duplicates(candidates)
    out = age_filter(out, max_age_hours=max_age_hours)
    out = self_post_filter(out, viewer_id)
    if seen_post_ids:
        out = previously_seen_filter(out, seen_post_ids)
    return out
