"""Candidate sources: Thunder-style in-network, Phoenix-style out-of-network."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from .types import Candidate

if TYPE_CHECKING:
    from store import Store


def thunder_source(store: "Store", user_id: str, limit_in_network: int = 200) -> list[Candidate]:
    """In-network: recent posts from accounts the user follows."""
    user = store.get_user(user_id)
    if not user or not user.following_ids:
        return []
    post_ids = store.get_recent_post_ids_for_following(user.following_ids, limit_per_author=20)
    posts = store.get_posts(post_ids[:limit_in_network])
    users = store.get_users([p.author_id for p in posts.values()])
    out: list[Candidate] = []
    for pid, post in posts.items():
        author = users.get(post.author_id)
        engagement = store.get_engagement_counts(pid)
        engagement_counts = {k.value: v for k, v in engagement.items()}
        out.append(
            Candidate(
                post=post,
                author=author,
                source="in_network",
                engagement_counts=engagement_counts,
            )
        )
    return out


def phoenix_source(
    store: "Store", user_id: str, limit_oon: int = 150, friends_vs_global: float = 0.4
) -> list[Candidate]:
    """Out-of-network: global recent posts, excluding already-followed. Mix controlled by friends_vs_global."""
    user = store.get_user(user_id)
    following = set(user.following_ids) if user else set()
    all_ids = store.get_global_recent(limit=limit_oon * 2)
    posts = store.get_posts(all_ids)
    # Exclude in-network authors (optional: when friends_vs_global is low, we still want some OON)
    oon_ids = [
        pid for pid in all_ids
        if pid in posts and posts[pid].author_id not in following
    ][:limit_oon]
    if not oon_ids:
        return []
    posts_sub = store.get_posts(oon_ids)
    users = store.get_users([p.author_id for p in posts_sub.values()])
    out: list[Candidate] = []
    for pid, post in posts_sub.items():
        author = users.get(post.author_id)
        engagement = store.get_engagement_counts(pid)
        engagement_counts = {k.value: v for k, v in engagement.items()}
        out.append(
            Candidate(
                post=post,
                author=author,
                source="out_of_network",
                engagement_counts=engagement_counts,
            )
        )
    return out


def get_candidates(store: "Store", user_id: str, friends_vs_global: float, limits: tuple[int, int] = (200, 150)) -> list[Candidate]:
    """Merge in-network and OON candidates. friends_vs_global in [0,1]: higher = more OON."""
    in_net = thunder_source(store, user_id, limit_in_network=limits[0])
    oon = phoenix_source(store, user_id, limit_oon=limits[1], friends_vs_global=friends_vs_global)
    # Simple merge: in-network first, then OON (scoring will reorder)
    return in_net + oon
