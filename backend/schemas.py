"""Shared Pydantic schemas for posts, users, preferences, and ranking explainability."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------- Enums ----------
class PostType(str, Enum):
    ORIGINAL = "original"
    REPLY = "reply"
    REPOST = "repost"
    QUOTE = "quote"


class PersonaKind(str, Enum):
    FOUNDER = "founder"
    JOURNALIST = "journalist"
    MEME = "meme"
    TRADER = "trader"
    POLITICIAN = "politician"
    CULTURE = "culture"
    TECH = "tech"


class Topic(str, Enum):
    TECH = "tech"
    POLITICS = "politics"
    CULTURE = "culture"
    MEMES = "memes"
    FINANCE = "finance"
    NEWS = "news"
    OTHER = "other"


# ---------- User & Profile ----------
class UserBase(BaseModel):
    id: str
    handle: str
    display_name: str
    bio: str = ""
    persona_kind: PersonaKind | None = None
    topics: list[Topic] = Field(default_factory=list)
    avatar_url: str | None = None


class User(UserBase):
    following_ids: list[str] = Field(default_factory=list)
    followers_count: int = 0
    following_count: int = 0


# ---------- Post ----------
class PostBase(BaseModel):
    id: str
    author_id: str
    text: str
    post_type: PostType = PostType.ORIGINAL
    parent_id: str | None = None
    quoted_id: str | None = None
    topics: list[Topic] = Field(default_factory=list)
    created_at: float  # unix timestamp


class Post(PostBase):
    like_count: int = 0
    repost_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    view_count: int = 0


class PostWithAuthor(Post):
    author: User | None = None


# ---------- Engagement ----------
class EngagementType(str, Enum):
    LIKE = "like"
    REPOST = "repost"
    REPLY = "reply"
    QUOTE = "quote"
    PROFILE_CLICK = "profile_click"
    NOT_INTERESTED = "not_interested"


class Engagement(BaseModel):
    user_id: str
    post_id: str
    engagement_type: EngagementType
    created_at: float


# ---------- Notifications ----------
class NotificationType(str, Enum):
    LIKE = "like"
    REPOST = "repost"
    REPLY = "reply"
    QUOTE = "quote"
    FOLLOW = "follow"


class Notification(BaseModel):
    id: str
    recipient_id: str
    actor_id: str  # who did the action
    notification_type: NotificationType
    post_id: str | None = None  # for like/repost/reply/quote
    created_at: float


# ---------- Algorithm Preferences (tunable) ----------
class AlgorithmPreferences(BaseModel):
    """User-facing sliders that drive ranking. All in [0, 1] unless noted."""

    # Recency vs popularity: 0 = recency, 1 = popularity
    recency_vs_popularity: float = 0.3

    # Friends vs global: 0 = mostly following, 1 = more out-of-network
    friends_vs_global: float = 0.4

    # Niche vs viral: 0 = diverse/niche, 1 = viral/popular
    niche_vs_viral: float = 0.5

    # Topic weights (sum to 1 or used as relative weights)
    tech_weight: float = 0.2
    politics_weight: float = 0.2
    culture_weight: float = 0.2
    memes_weight: float = 0.2
    finance_weight: float = 0.2

    # Diversity: 0 = allow author stacking, 1 = strong author diversity
    diversity_strength: float = 0.6

    # Exploration: 0 = safe/filter-bubble, 1 = more exploration
    exploration: float = 0.3

    # Negative signal strength (down-rank not_interested / report)
    negative_signal_strength: float = 0.8


# ---------- Ranking Explainability ----------
class ActionScore(BaseModel):
    action: str
    weight: float
    probability: float
    contribution: float


class RankingExplanation(BaseModel):
    """Why this post appeared at this rank."""

    post_id: str
    final_score: float
    rank: int
    source: str  # "in_network" | "out_of_network"
    action_scores: list[ActionScore] = Field(default_factory=list)
    diversity_penalty: float = 0.0
    recency_boost: float = 0.0
    topic_boost: float = 0.0
    raw_breakdown: dict[str, Any] = Field(default_factory=dict)


# ---------- API Request/Response ----------
class FeedRequest(BaseModel):
    user_id: str
    preferences: AlgorithmPreferences | None = None
    limit: int = 50
    cursor: str | None = None
    include_explanations: bool = True


class FeedItem(BaseModel):
    post: PostWithAuthor
    ranking_explanation: RankingExplanation | None = None
    parent_post: PostWithAuthor | None = None  # for replies: the post being replied to
    quoted_post: PostWithAuthor | None = None  # for quote tweets: the quoted post


class FeedResponse(BaseModel):
    items: list[FeedItem]
    next_cursor: str | None = None
