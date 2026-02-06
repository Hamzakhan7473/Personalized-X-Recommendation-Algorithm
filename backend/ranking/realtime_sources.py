"""Optional real-time external sources: news APIs, (stub for tweets). Inject into feed when API keys are set."""

from __future__ import annotations

import os
import re
import time
from typing import TYPE_CHECKING

from schemas import Post, PostType, Topic, User

from .types import Candidate

if TYPE_CHECKING:
    pass  # no store dependency for news; optional twitter could use store for dedup


# Synthetic author for news / external content
NEWS_USER = User(
    id="news_api",
    handle="news_api",
    display_name="News",
    bio="Headlines from News API",
    topics=[Topic.NEWS],
    following_ids=[],
    followers_count=0,
    following_count=0,
)

# Category from News API -> our Topic
_CATEGORY_TO_TOPIC = {
    "business": Topic.FINANCE,
    "entertainment": Topic.CULTURE,
    "general": Topic.NEWS,
    "health": Topic.OTHER,
    "science": Topic.TECH,
    "sports": Topic.CULTURE,
    "technology": Topic.TECH,
}


def _sanitize_text(s: str, max_len: int = 280) -> str:
    if not s or not s.strip():
        return ""
    t = re.sub(r"\s+", " ", s.strip())
    if len(t) > max_len:
        t = t[: max_len - 3] + "..."
    return t


def _fetch_news_api(limit: int = 25) -> list[Candidate]:
    """Fetch top headlines from NewsAPI.org. Requires NEWS_API_KEY. Returns list of Candidates."""
    key = os.environ.get("NEWS_API_KEY", "").strip()
    if not key:
        return []
    try:
        import httpx
    except ImportError:
        return []

    category = os.environ.get("NEWS_API_CATEGORY", "general").strip().lower()
    country = os.environ.get("NEWS_API_COUNTRY", "us").strip().lower()
    # Top headlines: country or category, max 100
    params = {"apiKey": key, "pageSize": min(limit, 100)}
    if country and len(country) == 2:
        params["country"] = country
    if category in _CATEGORY_TO_TOPIC:
        params["category"] = category

    try:
        r = httpx.get("https://newsapi.org/v2/top-headlines", params=params, timeout=10.0)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    articles = data.get("articles") or []
    candidates: list[Candidate] = []
    now = time.time()
    for i, a in enumerate(articles[:limit]):
        title = (a.get("title") or "").strip()
        desc = (a.get("description") or "").strip()
        if not title:
            continue
        text = _sanitize_text(f"{title} {desc}" if desc else title, max_len=280)
        source_name = (a.get("source", {}) or {}).get("name") or "News"
        cat = (a.get("category") or category or "general").lower()
        topic = _CATEGORY_TO_TOPIC.get(cat, Topic.NEWS)
        published = a.get("publishedAt")
        try:
            if published:
                from datetime import datetime
                s = published.replace("Z", "+00:00")[:22]
                created_at = datetime.fromisoformat(s).timestamp()
            else:
                created_at = now - i * 60
        except Exception:
            created_at = now - i * 60

        post_id = f"news_{int(created_at)}_{i}"
        post = Post(
            id=post_id,
            author_id=NEWS_USER.id,
            text=text,
            post_type=PostType.ORIGINAL,
            parent_id=None,
            quoted_id=None,
            topics=[topic],
            created_at=created_at,
            like_count=0,
            repost_count=0,
            reply_count=0,
            quote_count=0,
            view_count=0,
        )
        # Optional: per-source display name
        author = User(
            id=NEWS_USER.id,
            handle=NEWS_USER.handle,
            display_name=source_name,
            bio=NEWS_USER.bio,
            topics=[topic],
            following_ids=[],
            followers_count=0,
            following_count=0,
        )
        candidates.append(
            Candidate(
                post=post,
                author=author,
                source="out_of_network",
                engagement_counts={"like": 0, "repost": 0, "reply": 0, "quote": 0},
            )
        )
    return candidates


def twitter_source_stub(limit: int = 20) -> list[Candidate]:
    """
    Stub for Twitter/X API. X API v2 requires approved developer access and has strict rate limits.
    To add real tweets:
    1. Get Bearer Token from developer.twitter.com (e.g. Free or Basic tier).
    2. Set TWITTER_BEARER_TOKEN in env.
    3. Call GET /2/tweets/search/recent with query (e.g. from topic/preferences).
    4. Map each tweet to Post (id=tweet id, author_id=author id, text=text, created_at=created_at).
    5. Create synthetic User from GET /2/users/:id or embed in tweet response.
    6. Return list[Candidate] with source='out_of_network'.
    """
    token = os.environ.get("TWITTER_BEARER_TOKEN", "").strip()
    if not token:
        return []
    # Placeholder: could add httpx get to api.twitter.com/2/tweets/search/recent
    return []


def get_realtime_candidates(limit: int = 25) -> list[Candidate]:
    """Merge candidates from all configured real-time APIs (news, optional twitter)."""
    out: list[Candidate] = []
    if os.environ.get("NEWS_API_KEY", "").strip():
        out.extend(_fetch_news_api(limit=limit))
    if os.environ.get("TWITTER_BEARER_TOKEN", "").strip():
        out.extend(twitter_source_stub(limit=min(limit, 20)))
    return out
