"""FastAPI app: feed API, preferences, users, posts, and ranking explainability."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ranking import HomeMixer
from schemas import (
    AlgorithmPreferences,
    Engagement,
    EngagementType,
    FeedRequest,
    FeedResponse,
    Post,
    PostType,
    Topic,
    User,
)
from store import Store

# -------- In-memory store (single process) --------
store = Store(retention_seconds=86400 * 14)
mixer = HomeMixer(store)
# Per-user algorithm preferences (persisted for session / process lifetime)
user_preferences: dict[str, AlgorithmPreferences] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    from seed import seed_store
    seed_store(store)
    yield


app = FastAPI(
    title="Personalized X Recommendation API",
    description="Tunable, inspectable ranking pipeline inspired by xai-org/x-algorithm",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- API models --------
class PreferencesUpdate(BaseModel):
    preferences: AlgorithmPreferences


# -------- Feed --------
@app.post("/api/feed", response_model=FeedResponse)
def get_feed(req: FeedRequest) -> FeedResponse:
    """Return ranked For You feed for the user with optional explanations."""
    if store.get_user(req.user_id) is None:
        raise HTTPException(404, "User not found")
    # Use request preferences if provided, else stored preferences, else defaults
    prefs = req.preferences or user_preferences.get(req.user_id)
    return mixer.get_feed(
        user_id=req.user_id,
        preferences=prefs,
        limit=req.limit,
        seen_post_ids=set(),
        include_explanations=req.include_explanations,
    )


@app.get("/api/feed/{user_id}", response_model=FeedResponse)
def get_feed_get(
    user_id: str,
    limit: int = 50,
    include_explanations: bool = True,
) -> FeedResponse:
    """GET variant of feed (uses stored or default preferences)."""
    if store.get_user(user_id) is None:
        raise HTTPException(404, "User not found")
    prefs = user_preferences.get(user_id)
    return mixer.get_feed(
        user_id=user_id,
        preferences=prefs,
        limit=limit,
        include_explanations=include_explanations,
    )


# -------- Algorithm preferences (tunable) --------
@app.get("/api/users/{user_id}/preferences", response_model=AlgorithmPreferences)
def get_preferences(user_id: str) -> AlgorithmPreferences:
    """Return current algorithm preferences for the user (defaults if not stored)."""
    return user_preferences.get(user_id, AlgorithmPreferences())


@app.put("/api/users/{user_id}/preferences", response_model=AlgorithmPreferences)
def put_preferences(user_id: str, body: PreferencesUpdate) -> AlgorithmPreferences:
    """Update algorithm preferences for the user. Stored in memory for process lifetime."""
    user_preferences[user_id] = body.preferences
    return body.preferences


# -------- Users --------
@app.get("/api/users/{user_id}", response_model=User)
def get_user(user_id: str) -> User:
    u = store.get_user(user_id)
    if u is None:
        raise HTTPException(404, "User not found")
    return u


@app.get("/api/users")
def list_users(limit: int = 100) -> dict[str, Any]:
    ids = store.list_user_ids()[:limit]
    users = [store.get_user(i) for i in ids if store.get_user(i)]
    return {"users": [u.model_dump() for u in users]}


# -------- Posts --------
class CreatePostBody(BaseModel):
    author_id: str
    text: str = Field(..., min_length=1, max_length=280)
    topics: list[str] = Field(default_factory=list, description="e.g. tech, politics, memes, finance, culture, news, other")


@app.post("/api/posts", response_model=Post)
def create_post(body: CreatePostBody) -> Post:
    """Create a new post. Returns the created post."""
    if store.get_user(body.author_id) is None:
        raise HTTPException(404, "Author not found")
    topic_list = []
    for t in body.topics:
        try:
            topic_list.append(Topic(t))
        except ValueError:
            pass
    post_id = f"p_{uuid.uuid4().hex[:12]}"
    post = Post(
        id=post_id,
        author_id=body.author_id,
        text=body.text.strip(),
        post_type=PostType.ORIGINAL,
        topics=topic_list,
        created_at=time.time(),
        like_count=0,
        repost_count=0,
        reply_count=0,
        quote_count=0,
        view_count=0,
    )
    store.add_post(post)
    return post


@app.get("/api/posts/{post_id}", response_model=Post)
def get_post(post_id: str) -> Post:
    p = store.get_post(post_id)
    if p is None:
        raise HTTPException(404, "Post not found")
    return p


# -------- Trends --------
@app.get("/api/trends")
def get_trends(limit: int = 10, max_age_hours: float = 168) -> dict[str, Any]:
    """Return trending topics from recent posts (topic -> count), sorted by count descending."""
    max_age_seconds = max_age_hours * 3600
    pairs = store.get_topic_counts(max_age_seconds=max_age_seconds, limit=limit)
    return {"trends": [{"topic": t, "count": c} for t, c in pairs]}


# -------- Follow / Unfollow --------
class FollowBody(BaseModel):
    target_id: str


@app.post("/api/users/{user_id}/follow", response_model=User)
def follow(user_id: str, body: FollowBody) -> User:
    """Add target to user's following list; update both users."""
    user = store.get_user(user_id)
    target = store.get_user(body.target_id)
    if user is None or target is None:
        raise HTTPException(404, "User or target not found")
    if body.target_id in user.following_ids:
        return user
    new_following = list(user.following_ids) + [body.target_id]
    user_updated = user.model_copy(update={"following_ids": new_following, "following_count": len(new_following)})
    target_updated = target.model_copy(update={"followers_count": target.followers_count + 1})
    store.update_user(user_updated)
    store.update_user(target_updated)
    return user_updated


@app.post("/api/users/{user_id}/unfollow", response_model=User)
def unfollow(user_id: str, body: FollowBody) -> User:
    """Remove target from user's following list; update both users."""
    user = store.get_user(user_id)
    target = store.get_user(body.target_id)
    if user is None or target is None:
        raise HTTPException(404, "User or target not found")
    if body.target_id not in user.following_ids:
        return user
    new_following = [x for x in user.following_ids if x != body.target_id]
    user_updated = user.model_copy(update={"following_ids": new_following, "following_count": len(new_following)})
    target_updated = target.model_copy(update={"followers_count": max(0, target.followers_count - 1)})
    store.update_user(user_updated)
    store.update_user(target_updated)
    return user_updated


# -------- Engagement --------
class EngageBody(BaseModel):
    user_id: str
    post_id: str
    engagement_type: str = Field(..., description="like | repost | reply | quote | not_interested")


@app.post("/api/engage")
def engage(body: EngageBody) -> dict[str, str]:
    """Record a like, repost, reply, quote, or not_interested. Updates feed on next request."""
    try:
        et = EngagementType(body.engagement_type)
    except ValueError:
        raise HTTPException(400, f"Invalid engagement_type: {body.engagement_type}")
    e = Engagement(
        user_id=body.user_id,
        post_id=body.post_id,
        engagement_type=et,
        created_at=time.time(),
    )
    store.add_engagement(e)
    return {"status": "ok", "engagement_type": body.engagement_type}


# -------- Explainability --------
@app.get("/api/explain/feed/{user_id}")
def explain_feed(user_id: str, limit: int = 20) -> FeedResponse:
    """Return feed with full ranking explanations for each item."""
    if store.get_user(user_id) is None:
        raise HTTPException(404, "User not found")
    prefs = user_preferences.get(user_id)
    return mixer.get_feed(
        user_id=user_id,
        preferences=prefs,
        limit=limit,
        include_explanations=True,
    )


# -------- Health --------
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
