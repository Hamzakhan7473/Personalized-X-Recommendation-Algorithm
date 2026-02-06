"""In-memory + SQLite-backed store for users, posts, and engagements. Thunder-like recent-post cache."""

from __future__ import annotations

import time
from typing import Iterator

from schemas import Engagement, EngagementType, Post, PostType, User


class Store:
    """Single source of truth for users, posts, engagements. Includes recent-post cache (Thunder-like)."""

    def __init__(self, retention_seconds: float = 86400 * 7):
        self._users: dict[str, User] = {}
        self._posts: dict[str, Post] = {}
        self._engagements: list[Engagement] = []
        self._retention_seconds = retention_seconds
        self._recent_by_author: dict[str, list[str]] = {}  # author_id -> [post_id]

    # ---- Users ----
    def add_user(self, user: User) -> None:
        self._users[user.id] = user

    def get_user(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_users(self, user_ids: list[str]) -> dict[str, User]:
        return {uid: self._users[uid] for uid in user_ids if uid in self._users}

    def list_user_ids(self) -> list[str]:
        return list(self._users.keys())

    def update_user(self, user: User) -> None:
        """Replace user (e.g. after follow/unfollow)."""
        self._users[user.id] = user

    # ---- Posts ----
    def add_post(self, post: Post) -> None:
        self._posts[post.id] = post
        aid = post.author_id
        if aid not in self._recent_by_author:
            self._recent_by_author[aid] = []
        self._recent_by_author[aid].append(post.id)

    def get_post(self, post_id: str) -> Post | None:
        return self._posts.get(post_id)

    def get_posts(self, post_ids: list[str]) -> dict[str, Post]:
        return {pid: self._posts[pid] for pid in post_ids if pid in self._posts}

    def iter_all_posts(self) -> Iterator[Post]:
        yield from self._posts.values()

    def get_recent_post_ids_for_following(
        self, following_ids: list[str], limit_per_author: int = 50, max_age_seconds: float | None = None
    ) -> list[str]:
        """Thunder-style: recent posts from followed accounts."""
        cutoff = (time.time() - (max_age_seconds or self._retention_seconds))
        out: list[str] = []
        for aid in following_ids:
            if aid not in self._recent_by_author:
                continue
            seen = 0
            for pid in reversed(self._recent_by_author[aid]):
                if seen >= limit_per_author:
                    break
                p = self._posts.get(pid)
                if p and p.created_at >= cutoff:
                    out.append(pid)
                    seen += 1
        return out

    def get_posts_by_author(self, author_id: str, limit: int = 50) -> list[Post]:
        """Posts by this author, newest first (for profile timeline)."""
        if author_id not in self._recent_by_author:
            return []
        pids = list(reversed(self._recent_by_author[author_id]))[:limit]
        posts = [self._posts[pid] for pid in pids if self._posts.get(pid)]
        return sorted(posts, key=lambda p: p.created_at, reverse=True)

    def get_global_recent(self, limit: int = 500, max_age_seconds: float | None = None) -> list[str]:
        """Global recent post IDs for OON candidate pool."""
        cutoff = (time.time() - (max_age_seconds or self._retention_seconds))
        acc: list[tuple[float, str]] = []
        for p in self._posts.values():
            if p.created_at >= cutoff and p.post_type == PostType.ORIGINAL:
                acc.append((p.created_at, p.id))
        acc.sort(reverse=True, key=lambda x: x[0])
        return [pid for _, pid in acc[:limit]]

    def get_topic_counts(self, max_age_seconds: float | None = None, limit: int = 20) -> list[tuple[str, int]]:
        """Return (topic, count) for recent posts, sorted by count descending."""
        cutoff = time.time() - (max_age_seconds or self._retention_seconds)
        counts: dict[str, int] = {}
        for p in self._posts.values():
            if p.created_at < cutoff:
                continue
            for t in p.topics:
                counts[t.value] = counts.get(t.value, 0) + 1
        sorted_topics = sorted(counts.items(), key=lambda x: -x[1])
        return sorted_topics[:limit]

    # ---- Engagements ----
    def add_engagement(self, e: Engagement) -> None:
        self._engagements.append(e)

    def get_engagement_counts(self, post_id: str) -> dict[EngagementType, int]:
        counts = {t: 0 for t in EngagementType}
        for e in self._engagements:
            if e.post_id == post_id:
                counts[e.engagement_type] = counts.get(e.engagement_type, 0) + 1
        return counts

    def get_user_engagement_post_ids(self, user_id: str, limit: int = 200) -> list[str]:
        """Post IDs this user liked/reposted/replied to (for engagement history)."""
        seen: set[str] = set()
        out: list[str] = []
        for e in reversed(self._engagements):
            if e.user_id != user_id:
                continue
            if e.post_id in seen:
                continue
            seen.add(e.post_id)
            out.append(e.post_id)
            if len(out) >= limit:
                break
        return out

    def get_negative_engagement_post_ids(self, user_id: str, limit: int = 100) -> list[str]:
        """Posts this user marked not_interested (or similar)."""
        out: list[str] = []
        for e in reversed(self._engagements):
            if e.user_id != user_id or e.engagement_type != EngagementType.NOT_INTERESTED:
                continue
            out.append(e.post_id)
            if len(out) >= limit:
                break
        return out
