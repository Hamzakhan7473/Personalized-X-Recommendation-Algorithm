"""SQLite persistence for users, posts, engagements, preferences, and sessions. Data survives restart."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

from schemas import (
    AlgorithmPreferences,
    Engagement,
    EngagementType,
    Notification,
    NotificationType,
    Post,
    PostType,
    Topic,
    User,
)
from schemas import PersonaKind


def _get_db_path() -> Path:
    path = Path(__file__).resolve().parent / "data"
    path.mkdir(exist_ok=True)
    return path / "app.db"


def init_db(db_path: Path | None = None) -> None:
    """Create tables if they do not exist."""
    conn = sqlite3.connect(db_path or _get_db_path())
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                handle TEXT NOT NULL,
                display_name TEXT NOT NULL,
                bio TEXT DEFAULT '',
                persona_kind TEXT,
                topics TEXT DEFAULT '[]',
                avatar_url TEXT,
                following_ids TEXT DEFAULT '[]',
                followers_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                author_id TEXT NOT NULL,
                text TEXT NOT NULL,
                post_type TEXT DEFAULT 'original',
                parent_id TEXT,
                quoted_id TEXT,
                topics TEXT DEFAULT '[]',
                created_at REAL NOT NULL,
                like_count INTEGER DEFAULT 0,
                repost_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                quote_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS engagements (
                user_id TEXT NOT NULL,
                post_id TEXT NOT NULL,
                engagement_type TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS preferences (
                user_id TEXT PRIMARY KEY,
                prefs TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                recipient_id TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                post_id TEXT,
                created_at REAL NOT NULL
            );
        """)
        conn.commit()
    finally:
        conn.close()


def load_into_store(store, db_path: Path | None = None) -> bool:
    """Load users, posts, engagements from DB into store. Returns True if any data was loaded."""
    path = db_path or _get_db_path()
    if not path.exists():
        return False
    conn = sqlite3.connect(path)
    try:
        cur = conn.execute("SELECT id, handle, display_name, bio, persona_kind, topics, avatar_url, following_ids, followers_count, following_count FROM users")
        for row in cur:
            uid, handle, display_name, bio, persona_kind_str, topics_json, avatar_url, following_json, fc, foc = row
            topics = [Topic(t) for t in json.loads(topics_json or "[]") if t in [e.value for e in Topic]]
            following_ids = json.loads(following_json or "[]")
            try:
                persona_kind = PersonaKind(persona_kind_str) if persona_kind_str else None
            except ValueError:
                persona_kind = None
            store.add_user(User(
                id=uid, handle=handle, display_name=display_name, bio=bio or "",
                persona_kind=persona_kind, topics=topics, avatar_url=avatar_url,
                following_ids=following_ids, followers_count=fc or 0, following_count=foc or 0,
            ))
        cur = conn.execute("SELECT id, author_id, text, post_type, parent_id, quoted_id, topics, created_at, like_count, repost_count, reply_count, quote_count, view_count FROM posts")
        for row in cur:
            pid, author_id, text, post_type, parent_id, quoted_id, topics_json, created_at, lc, rc, rpc, qc, vc = row
            try:
                pt = PostType(post_type or "original")
            except ValueError:
                pt = PostType.ORIGINAL
            topics = [Topic(t) for t in json.loads(topics_json or "[]") if t in [e.value for e in Topic]]
            store.add_post(Post(
                id=pid, author_id=author_id, text=text, post_type=pt,
                parent_id=parent_id, quoted_id=quoted_id, topics=topics, created_at=created_at,
                like_count=lc or 0, repost_count=rc or 0, reply_count=rpc or 0, quote_count=qc or 0, view_count=vc or 0,
            ))
        cur = conn.execute("SELECT user_id, post_id, engagement_type, created_at FROM engagements ORDER BY created_at ASC")
        for row in cur:
            uid, pid, etype, created_at = row
            try:
                et = EngagementType(etype)
            except ValueError:
                continue
            store.add_engagement(Engagement(user_id=uid, post_id=pid, engagement_type=et, created_at=created_at))
        return bool(store.list_user_ids())
    finally:
        conn.close()


def persist_user(user: User, db_path: Path | None = None) -> None:
    path = db_path or _get_db_path()
    conn = sqlite3.connect(path)
    try:
        topics_json = json.dumps([t.value for t in user.topics])
        following_json = json.dumps(user.following_ids)
        conn.execute(
            """INSERT OR REPLACE INTO users (id, handle, display_name, bio, persona_kind, topics, avatar_url, following_ids, followers_count, following_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user.id, user.handle, user.display_name, user.bio, getattr(user.persona_kind, "value", None) if user.persona_kind else None,
             topics_json, user.avatar_url, following_json, user.followers_count, user.following_count),
        )
        conn.commit()
    finally:
        conn.close()


def persist_post(post: Post, db_path: Path | None = None) -> None:
    path = db_path or _get_db_path()
    conn = sqlite3.connect(path)
    try:
        topics_json = json.dumps([t.value for t in post.topics])
        conn.execute(
            """INSERT OR REPLACE INTO posts (id, author_id, text, post_type, parent_id, quoted_id, topics, created_at, like_count, repost_count, reply_count, quote_count, view_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (post.id, post.author_id, post.text, post.post_type.value, post.parent_id, post.quoted_id, topics_json,
             post.created_at, post.like_count, post.repost_count, post.reply_count, post.quote_count, post.view_count),
        )
        conn.commit()
    finally:
        conn.close()


def persist_engagement(e: Engagement, db_path: Path | None = None) -> None:
    path = db_path or _get_db_path()
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT INTO engagements (user_id, post_id, engagement_type, created_at) VALUES (?, ?, ?, ?)",
            (e.user_id, e.post_id, e.engagement_type.value, e.created_at),
        )
        conn.commit()
    finally:
        conn.close()


def load_preferences(db_path: Path | None = None) -> dict[str, AlgorithmPreferences]:
    path = db_path or _get_db_path()
    if not path.exists():
        return {}
    conn = sqlite3.connect(path)
    try:
        cur = conn.execute("SELECT user_id, prefs FROM preferences")
        out = {}
        for user_id, prefs_json in cur:
            try:
                out[user_id] = AlgorithmPreferences.model_validate(json.loads(prefs_json))
            except Exception:
                pass
        return out
    finally:
        conn.close()


def persist_preferences(user_id: str, prefs: AlgorithmPreferences, db_path: Path | None = None) -> None:
    path = db_path or _get_db_path()
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO preferences (user_id, prefs) VALUES (?, ?)",
            (user_id, prefs.model_dump_json()),
        )
        conn.commit()
    finally:
        conn.close()


def persist_session(session_id: str, user_id: str, db_path: Path | None = None) -> None:
    path = db_path or _get_db_path()
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO sessions (session_id, user_id, created_at) VALUES (?, ?, ?)",
            (session_id, user_id, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_id_for_session(session_id: str, db_path: Path | None = None) -> str | None:
    path = db_path or _get_db_path()
    if not path.exists():
        return None
    conn = sqlite3.connect(path)
    try:
        cur = conn.execute("SELECT user_id FROM sessions WHERE session_id = ?", (session_id,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def persist_notification(n: Notification, db_path: Path | None = None) -> None:
    path = db_path or _get_db_path()
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT INTO notifications (id, recipient_id, actor_id, notification_type, post_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (n.id, n.recipient_id, n.actor_id, n.notification_type.value, n.post_id, n.created_at),
        )
        conn.commit()
    finally:
        conn.close()


def get_notifications(recipient_id: str, limit: int = 50, db_path: Path | None = None) -> list[Notification]:
    path = db_path or _get_db_path()
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    try:
        cur = conn.execute(
            "SELECT id, recipient_id, actor_id, notification_type, post_id, created_at FROM notifications WHERE recipient_id = ? ORDER BY created_at DESC LIMIT ?",
            (recipient_id, limit),
        )
        out = []
        for row in cur:
            nid, rec, actor, ntype, post_id, created_at = row
            try:
                out.append(Notification(
                    id=nid, recipient_id=rec, actor_id=actor, notification_type=NotificationType(ntype),
                    post_id=post_id, created_at=created_at,
                ))
            except ValueError:
                continue
        return out
    finally:
        conn.close()
