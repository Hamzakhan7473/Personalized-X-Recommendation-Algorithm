"""FastAPI app: feed API, preferences, users, posts, ranking explainability, auth, persistence."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load backend/.env so GEMINI_API_KEY and OPENAI_API_KEY are available
load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ranking import HomeMixer
from schemas import (
    AlgorithmPreferences,
    Engagement,
    EngagementType,
    FeedRequest,
    FeedResponse,
    FeedItem,
    Notification,
    NotificationType,
    Post,
    PostType,
    Topic,
    User,
    PostWithAuthor,
)
from store import Store
import db
from llm_provider import generate_post as llm_generate_post, generate_reply as llm_generate_reply, is_llm_available

# -------- Store + persistence --------
store = Store(retention_seconds=86400 * 14)
mixer = HomeMixer(store)
user_preferences: dict[str, AlgorithmPreferences] = {}
DB_PATH = db._get_db_path()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db(DB_PATH)
    try:
        has_data = db.load_into_store(store, DB_PATH)
    except Exception:
        has_data = False
    if not has_data or len(store.list_user_ids()) == 0:
        from seed import seed_store
        engagements = seed_store(store)
        for uid in store.list_user_ids():
            u = store.get_user(uid)
            if u:
                db.persist_user(u, DB_PATH)
        for post in store.iter_all_posts():
            db.persist_post(post, DB_PATH)
        for e in engagements:
            db.persist_engagement(e, DB_PATH)
        from seed import seed_llm
        seed_llm(store, DB_PATH)
    user_preferences.update(db.load_preferences(DB_PATH))
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


# -------- Auth --------
class LoginBody(BaseModel):
    handle: str


def get_current_user_id(authorization: str | None = Header(None)) -> str | None:
    """Resolve user id from Authorization: Bearer <session_id>. Returns None if missing/invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    if not token:
        return None
    return db.get_user_id_for_session(token, DB_PATH)


VALID_HANDLES = ("me", "alice_dev", "bob_trades", "carol_news", "dave_memes", "eve_founder")


@app.post("/api/auth/login")
def login(body: LoginBody) -> dict[str, Any]:
    """Log in by handle or user id (e.g. me, u0, alice_dev). Returns user and session_id (use as Bearer token)."""
    raw = body.handle.strip()
    if not raw:
        raise HTTPException(400, "Handle is required. Try: me, alice_dev, bob_trades, carol_news, dave_memes, eve_founder")
    lookup = raw.lower()
    # Find by user id (e.g. u0, u1)
    user = store.get_user(lookup) if lookup.startswith("u") and len(lookup) <= 4 else None
    if user is None:
        users = [store.get_user(uid) for uid in store.list_user_ids() if store.get_user(uid)]
        user = next((u for u in users if u.handle.lower() == lookup), None)
    if user is None:
        raise HTTPException(
            404,
            f"No user with handle or id '{raw}'. Valid handles: {', '.join(VALID_HANDLES)}",
        )
    session_id = uuid.uuid4().hex
    db.persist_session(session_id, user.id, DB_PATH)
    return {"user": user.model_dump(), "session_id": session_id}


@app.get("/api/auth/me", response_model=User)
def auth_me(authorization: str | None = Header(None)) -> User:
    """Return current user from session. 401 if not logged in."""
    user_id = get_current_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Not logged in")
    u = store.get_user(user_id)
    if u is None:
        raise HTTPException(401, "User not found")
    return u


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
    following_only: bool = False,
) -> FeedResponse:
    """GET variant of feed. following_only=True for 'Following' tab (in-network only)."""
    if store.get_user(user_id) is None:
        raise HTTPException(404, "User not found")
    prefs = user_preferences.get(user_id)
    return mixer.get_feed(
        user_id=user_id,
        preferences=prefs,
        limit=limit,
        include_explanations=include_explanations,
        following_only=following_only,
    )


# -------- Algorithm preferences (tunable) --------
@app.get("/api/users/{user_id}/preferences", response_model=AlgorithmPreferences)
def get_preferences(user_id: str) -> AlgorithmPreferences:
    """Return current algorithm preferences for the user (defaults if not stored)."""
    return user_preferences.get(user_id, AlgorithmPreferences())


@app.put("/api/users/{user_id}/preferences", response_model=AlgorithmPreferences)
def put_preferences(user_id: str, body: PreferencesUpdate) -> AlgorithmPreferences:
    """Update algorithm preferences for the user. Persisted to DB."""
    user_preferences[user_id] = body.preferences
    db.persist_preferences(user_id, body.preferences, DB_PATH)
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


@app.get("/api/users/{user_id}/posts", response_model=FeedResponse)
def get_user_posts(user_id: str, limit: int = 50) -> FeedResponse:
    """Profile timeline: posts by this user, newest first."""
    if store.get_user(user_id) is None:
        raise HTTPException(404, "User not found")
    author = store.get_user(user_id)
    posts = store.get_posts_by_author(user_id, limit=limit)
    items: list[FeedItem] = []
    for post in posts:
        counts = store.get_engagement_counts(post.id)
        engagement_counts = {k.value: v for k, v in counts.items()}
        data = post.model_dump()
        data["like_count"] = engagement_counts.get("like", 0)
        data["repost_count"] = engagement_counts.get("repost", 0)
        data["reply_count"] = engagement_counts.get("reply", 0)
        data["quote_count"] = engagement_counts.get("quote", 0)
        post_wa = PostWithAuthor(**data, author=author)
        parent_post = None
        if post.parent_id:
            parent_p = store.get_post(post.parent_id)
            if parent_p:
                parent_a = store.get_user(parent_p.author_id)
                parent_post = PostWithAuthor(**parent_p.model_dump(), author=parent_a)
        quoted_post = None
        if post.quoted_id:
            quoted_p = store.get_post(post.quoted_id)
            if quoted_p:
                quoted_a = store.get_user(quoted_p.author_id)
                quoted_post = PostWithAuthor(**quoted_p.model_dump(), author=quoted_a)
        items.append(FeedItem(post=post_wa, ranking_explanation=None, parent_post=parent_post, quoted_post=quoted_post))
    return FeedResponse(items=items, next_cursor=None)


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
    db.persist_post(post, DB_PATH)
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
    db.persist_user(user_updated, DB_PATH)
    db.persist_user(target_updated, DB_PATH)
    # Notify the user who was followed
    notif = Notification(
        id=f"n_{uuid.uuid4().hex[:12]}",
        recipient_id=body.target_id,
        actor_id=user_id,
        notification_type=NotificationType.FOLLOW,
        post_id=None,
        created_at=time.time(),
    )
    db.persist_notification(notif, DB_PATH)
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
    db.persist_user(user_updated, DB_PATH)
    db.persist_user(target_updated, DB_PATH)
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
    db.persist_engagement(e, DB_PATH)
    # Notify post author (unless self-engagement)
    post = store.get_post(body.post_id)
    if post and post.author_id != body.user_id and et in (EngagementType.LIKE, EngagementType.REPOST, EngagementType.REPLY, EngagementType.QUOTE):
        ntype = NotificationType(et.value)
        notif = Notification(
            id=f"n_{uuid.uuid4().hex[:12]}",
            recipient_id=post.author_id,
            actor_id=body.user_id,
            notification_type=ntype,
            post_id=body.post_id,
            created_at=e.created_at,
        )
        db.persist_notification(notif, DB_PATH)
    return {"status": "ok", "engagement_type": body.engagement_type}


# -------- Notifications --------
@app.get("/api/notifications")
def get_notifications(authorization: str | None = Header(None), limit: int = 50) -> dict[str, Any]:
    """Return notifications for the current user (from session). Requires Authorization: Bearer <session_id>."""
    user_id = get_current_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Not logged in")
    notifications = db.get_notifications(user_id, limit=limit, db_path=DB_PATH)
    # Hydrate actor and post for display
    out = []
    for n in notifications:
        actor = store.get_user(n.actor_id)
        post = store.get_post(n.post_id) if n.post_id else None
        out.append({
            "id": n.id,
            "notification_type": n.notification_type.value,
            "actor": actor.model_dump() if actor else None,
            "post_id": n.post_id,
            "post_preview": post.text[:80] + "..." if post and len(post.text) > 80 else (post.text if post else None),
            "created_at": n.created_at,
        })
    return {"notifications": out}


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


# -------- Real-time LLM (OpenAI / Gemini) --------
@app.get("/api/llm/status")
def llm_status() -> dict[str, Any]:
    """Return whether an LLM is available (OPENAI_API_KEY or GEMINI_API_KEY set)."""
    return {"available": is_llm_available()}


class GeneratePostBody(BaseModel):
    user_id: str
    publish: bool = Field(False, description="If true, create the post so it appears in feeds immediately.")


@app.post("/api/llm/generate-post")
def llm_generate_post_endpoint(body: GeneratePostBody) -> dict[str, Any]:
    """Generate a tweet as the given user. Optionally publish it so the feed updates in real time. Requires OPENAI_API_KEY or GEMINI_API_KEY."""
    try:
        if not is_llm_available():
            raise HTTPException(503, "No LLM configured. Set OPENAI_API_KEY or GEMINI_API_KEY in the environment.")
        user = store.get_user(body.user_id)
        if user is None:
            raise HTTPException(404, "User not found")
        recent_ids = store.get_global_recent(limit=20)
        context = [store.get_post(pid) for pid in recent_ids if store.get_post(pid)]
        context = [p for p in context if p]
        text, err = llm_generate_post(user, context)
        if not text:
            raise HTTPException(502, err or "LLM returned no text. Check API key and model.")
        out: dict[str, Any] = {"text": text}
        if body.publish:
            post_id = f"p_{uuid.uuid4().hex[:12]}"
            post = Post(
                id=post_id,
                author_id=body.user_id,
                text=text,
                post_type=PostType.ORIGINAL,
                topics=user.topics[:3] if user.topics else [],
                created_at=time.time(),
                like_count=0,
                repost_count=0,
                reply_count=0,
                quote_count=0,
                view_count=0,
            )
            store.add_post(post)
            db.persist_post(post, DB_PATH)
            out["post_id"] = post_id
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Server error: {str(e)[:200]}")


class GenerateReplyBody(BaseModel):
    user_id: str
    post_id: str


@app.post("/api/llm/generate-reply")
def llm_generate_reply_endpoint(body: GenerateReplyBody) -> dict[str, Any]:
    """Generate a reply to a post as the given user. Does not publish; returns text only."""
    if not is_llm_available():
        raise HTTPException(503, "No LLM configured. Set OPENAI_API_KEY or GEMINI_API_KEY.")
    user = store.get_user(body.user_id)
    parent = store.get_post(body.post_id)
    if user is None or parent is None:
        raise HTTPException(404, "User or post not found")
    author = store.get_user(parent.author_id)
    handle = author.handle if author else parent.author_id
    text, err = llm_generate_reply(user, parent, handle)
    if not text:
        raise HTTPException(502, err or "LLM returned no text.")
    return {"text": text}


# -------- Health --------
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
