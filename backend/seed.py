"""Seed store with synthetic users, posts, and optional LLM-generated content."""

from __future__ import annotations

import os
import random
import time
from pathlib import Path
from uuid import uuid4

from schemas import Engagement, EngagementType, Post, PostType, Topic, User
from schemas import PersonaKind
from store import Store


def _id() -> str:
    return str(uuid4())[:8]


PERSONA_IDS = ["u1", "u2", "u3", "u4", "u5"]


def seed_engagements(store: Store) -> list[Engagement]:
    """Add synthetic likes and reposts so the feed has realistic engagement signals and ranking varies."""
    engagements: list[Engagement] = []
    post_ids = [p.id for p in store.iter_all_posts()]
    base_ts = time.time() - 86400 * 2
    for pid in post_ids:
        post = store.get_post(pid)
        if not post:
            continue
        author_id = post.author_id
        # Other personas who can engage (not self)
        others = [u for u in PERSONA_IDS if u != author_id]
        if not others:
            continue
        # 1–4 likes from random others
        for _ in range(random.randint(1, 4)):
            uid = random.choice(others)
            engagements.append(
                Engagement(user_id=uid, post_id=pid, engagement_type=EngagementType.LIKE, created_at=base_ts + random.uniform(0, 3600))
            )
        # 0–2 reposts
        for _ in range(random.randint(0, 2)):
            uid = random.choice(others)
            engagements.append(
                Engagement(user_id=uid, post_id=pid, engagement_type=EngagementType.REPOST, created_at=base_ts + random.uniform(3600, 7200))
            )
    for e in engagements:
        store.add_engagement(e)
    return engagements


def seed_llm(store: Store, db_path: Path | None = None) -> None:
    """Optionally add LLM-generated posts and replies. Set USE_LLM_SEED=1 and API keys. Guardrails: max posts per persona, no spam."""
    if not os.environ.get("USE_LLM_SEED"):
        return
    try:
        from llm_provider import generate_post as llm_generate_post, generate_reply as llm_generate_reply, is_llm_available
    except ImportError:
        return
    if not is_llm_available():
        return
    import db as db_module
    path = db_path or db_module._get_db_path()
    recent_ids = store.get_global_recent(limit=30)
    context = [store.get_post(pid) for pid in recent_ids if store.get_post(pid)]
    context = [p for p in context if p]
    base_ts = time.time() - 3600
    # 1) One extra post per persona (u1-u5)
    for uid in PERSONA_IDS:
        user = store.get_user(uid)
        if not user:
            continue
        text, _ = llm_generate_post(user, context)
        if not text:
            continue
        post_id = f"p_llm_{uuid4().hex[:10]}"
        post = Post(
            id=post_id,
            author_id=uid,
            text=text[:280],
            post_type=PostType.ORIGINAL,
            topics=user.topics[:3] if user.topics else [],
            created_at=base_ts,
            like_count=0,
            repost_count=0,
            reply_count=0,
            quote_count=0,
            view_count=0,
        )
        store.add_post(post)
        db_module.persist_post(post, path)
        context.append(post)
    # 2) A few reply posts (LLM-generated)
    all_post_ids = [p.id for p in store.iter_all_posts()]
    for _ in range(min(5, len(all_post_ids) * 2)):
        parent = store.get_post(random.choice(all_post_ids))
        if not parent or parent.post_type != PostType.ORIGINAL:
            continue
        replier_id = random.choice([u for u in PERSONA_IDS if u != parent.author_id])
        replier = store.get_user(replier_id)
        author = store.get_user(parent.author_id)
        if not replier or not author:
            continue
        text, _ = llm_generate_reply(replier, parent, author.handle)
        if not text:
            continue
        reply_id = f"p_llm_r_{uuid4().hex[:8]}"
        reply = Post(
            id=reply_id,
            author_id=replier_id,
            text=text[:280],
            post_type=PostType.REPLY,
            parent_id=parent.id,
            topics=replier.topics[:2] if replier.topics else [],
            created_at=base_ts + random.uniform(60, 600),
            like_count=0,
            repost_count=0,
            reply_count=0,
            quote_count=0,
            view_count=0,
        )
        store.add_post(reply)
        db_module.persist_post(reply, path)


def seed_store(store: Store) -> list[Engagement]:
    """Create synthetic users, posts, and engagement cascades so the feed has content and ranking signals."""
    base = time.time() - 86400 * 3  # spread over 3 days

    users = [
        User(
            id="u1",
            handle="alice_dev",
            display_name="Alice",
            bio="Builder. Tech.",
            persona_kind=PersonaKind.TECH,
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
            persona_kind=PersonaKind.TRADER,
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
            persona_kind=PersonaKind.JOURNALIST,
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
            persona_kind=PersonaKind.MEME,
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
            persona_kind=PersonaKind.FOUNDER,
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
            persona_kind=None,
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

    # Synthetic engagement cascades: likes and reposts so ranking has realistic signals
    return seed_engagements(store)
