"""Seed store with synthetic users and posts (no LLM yet). LLM personas in personas.py."""

from __future__ import annotations

import time
from uuid import uuid4

from schemas import Post, PostType, Topic, User
from store import Store


def _id() -> str:
    return str(uuid4())[:8]


def seed_store(store: Store) -> None:
    """Create synthetic users and posts so the feed has content."""
    base = time.time() - 86400 * 3  # spread over 3 days

    users = [
        User(
            id="u1",
            handle="alice_dev",
            display_name="Alice",
            bio="Builder. Tech.",
            topics=[Topic.TECH],
            following_ids=["u2", "u3", "u5"],
            followers_count=100,
            following_count=3,
        ),
        User(
            id="u2",
            handle="bob_trades",
            display_name="Bob",
            bio="Markets. Finance.",
            topics=[Topic.FINANCE],
            following_ids=["u1", "u4"],
            followers_count=200,
            following_count=2,
        ),
        User(
            id="u3",
            handle="carol_news",
            display_name="Carol",
            bio="Journalist.",
            topics=[Topic.NEWS, Topic.POLITICS],
            following_ids=["u1", "u2", "u4", "u5"],
            followers_count=500,
            following_count=4,
        ),
        User(
            id="u4",
            handle="dave_memes",
            display_name="Dave",
            bio="Memes.",
            topics=[Topic.MEMES, Topic.CULTURE],
            following_ids=["u1", "u3"],
            followers_count=1000,
            following_count=2,
        ),
        User(
            id="u5",
            handle="eve_founder",
            display_name="Eve",
            bio="Founder. Startup.",
            topics=[Topic.TECH, Topic.FINANCE],
            following_ids=["u1", "u2", "u3"],
            followers_count=300,
            following_count=3,
        ),
        User(
            id="u0",
            handle="me",
            display_name="Me",
            bio="The viewer.",
            topics=[],
            following_ids=["u1", "u2", "u3", "u4", "u5"],
            followers_count=0,
            following_count=5,
        ),
    ]

    for u in users:
        store.add_user(u)

    posts = [
        ("u1", "Ship fast, iterate. Broken in prod beats perfect in a doc.", [Topic.TECH], 0),
        ("u1", "We're hiring engineers. DM if you like Python and infra.", [Topic.TECH], 1),
        ("u2", "Markets are forward-looking. This dip is noise.", [Topic.FINANCE], 2),
        ("u2", "Long $BTC. Thread on why (1/5)", [Topic.FINANCE], 3),
        ("u3", "Breaking: new policy announced today. More at 6.", [Topic.NEWS, Topic.POLITICS], 4),
        ("u3", "Interview with the minister. Key quotes inside.", [Topic.POLITICS], 5),
        ("u4", "me explaining my portfolio to my cat", [Topic.MEMES], 6),
        ("u4", "POV: you're a dev and the stakeholder says 'just one more thing'", [Topic.MEMES, Topic.TECH], 7),
        ("u5", "Raising our seed round. Grateful for the belief.", [Topic.TECH, Topic.FINANCE], 8),
        ("u5", "What we learned in YC: distribution > product in week 1.", [Topic.TECH], 9),
        ("u1", "Hot take: types are documentation.", [Topic.TECH], 10),
        ("u2", "DCA is boring. Boring wins.", [Topic.FINANCE], 11),
        ("u3", "Fact-check: the claim going viral is false. Here's the source.", [Topic.NEWS], 12),
        ("u4", "nobody: absolutely nobody: me at 2am: 'what if we tried kubernetes'", [Topic.MEMES, Topic.TECH], 13),
        ("u5", "We hit 10k users today. On to 100k.", [Topic.TECH], 14),
    ]

    for i, (author_id, text, topics, offset) in enumerate(posts):
        created = base + offset * 3600 * 2
        post = Post(
            id=f"p{i}",
            author_id=author_id,
            text=text,
            post_type=PostType.ORIGINAL,
            topics=topics,
            created_at=created,
            like_count=0,
            repost_count=0,
            reply_count=0,
            quote_count=0,
            view_count=0,
        )
        store.add_post(post)
