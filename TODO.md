# Project TODO – Make It Work

## Backend (start here)

- [x] **Persist user preferences** – PUT `/api/users/{user_id}/preferences` stored in `user_preferences` dict; GET feed uses stored prefs.
- [x] **POST /api/posts** – Create a post (author_id, text, topics). GET **/api/trends** – Return trending topics (topic counts from recent posts).
- [x] **Follow / unfollow** – POST `/api/users/{user_id}/follow` and `/unfollow` with target_id; update `User.following_ids` in store.
- [ ] **Optional persistence** – SQLite (or aiosqlite) for users, posts, engagements so data survives server restart.
- [x] **Docs** – Link to `/docs` (OpenAPI) in README; endpoints documented.

## Frontend (after backend is solid)

- [x] **Scaffold Next.js** – `frontend/` with Next.js 14, API client, `NEXT_PUBLIC_API_URL`.
- [x] **Home feed** – Fetch `/api/feed`, render posts with author and engagement counts (like, repost, reply).
- [x] **Preference sliders** – Recency vs popularity, friends vs global, diversity; save to backend and refresh feed.
- [x] **Profiles + engagement** – <code>/users</code> page lists users with follow/unfollow; like/repost in feed.
- [x] **Explainability** – Toggle “why this post” (source, rank, score, diversity penalty, recency boost).

## Current status

- **Backend**: Full API: feed, preferences, users, posts (create), trends, follow/unfollow, engage. Seed on startup. Optional: SQLite persistence.
- **Frontend**: Next.js app with feed, preference sliders, trends, like/repost/reply, ranking explainability. Run: `cd frontend && npm install && npm run dev`.
