"""FastAPI app: feed API, preferences, users, posts, and ranking explainability."""

from __future__ import annotations

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
    User,
)
from store import Store

# -------- In-memory store (single process) --------
store = Store(retention_seconds=86400 * 14)
mixer = HomeMixer(store)


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
    return mixer.get_feed(
        user_id=req.user_id,
        preferences=req.preferences,
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
    """GET variant of feed (uses default preferences)."""
    if store.get_user(user_id) is None:
        raise HTTPException(404, "User not found")
    return mixer.get_feed(
        user_id=user_id,
        preferences=None,
        limit=limit,
        include_explanations=include_explanations,
    )


# -------- Algorithm preferences (tunable) --------
@app.get("/api/users/{user_id}/preferences", response_model=AlgorithmPreferences)
def get_preferences(user_id: str) -> AlgorithmPreferences:
    """Return current algorithm preferences for the user (defaults if not stored)."""
    # In-memory: we could persist per-user prefs; for now return defaults
    return AlgorithmPreferences()


@app.put("/api/users/{user_id}/preferences", response_model=AlgorithmPreferences)
def put_preferences(user_id: str, body: PreferencesUpdate) -> AlgorithmPreferences:
    """Update algorithm preferences for the user. Pass preferences in body."""
    # Persist in app state or DB; for now we just echo and use in next feed request
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
@app.get("/api/posts/{post_id}", response_model=Post)
def get_post(post_id: str) -> Post:
    p = store.get_post(post_id)
    if p is None:
        raise HTTPException(404, "Post not found")
    return p


# -------- Engagement --------
class EngageBody(BaseModel):
    user_id: str
    post_id: str
    engagement_type: str = Field(..., description="like | repost | reply | quote | not_interested")


@app.post("/api/engage")
def engage(body: EngageBody) -> dict[str, str]:
    """Record a like, repost, reply, quote, or not_interested. Updates feed on next request."""
    import time
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
    return mixer.get_feed(
        user_id=user_id,
        preferences=None,
        limit=limit,
        include_explanations=True,
    )


# -------- Health --------
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
