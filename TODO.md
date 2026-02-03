# Project TODO – Make It Work

## Backend (start here)

- [x] **Persist user preferences** – PUT `/api/users/{user_id}/preferences` stored in `user_preferences` dict; GET feed uses stored prefs.
- [ ] **POST /api/posts** – Create a post (author_id, text, topics). GET **/api/trends** – Return trending topics (e.g. topic counts from recent posts).
- [ ] **Follow / unfollow** – POST `/api/users/{user_id}/follow` and `/unfollow` with target_id; update `User.following_ids` in store.
- [ ] **Optional persistence** – SQLite (or aiosqlite) for users, posts, engagements so data survives server restart.
- [ ] **Docs** – Add link to `/docs` (OpenAPI) in README; verify all endpoints in Swagger.

## Frontend (after backend is solid)

- [ ] **Scaffold Next.js** – Create `frontend/` with Next.js, API client, env for `NEXT_PUBLIC_API_URL`.
- [ ] **Home feed** – Fetch `/api/feed`, render posts with author and engagement counts (like, repost, reply).
- [ ] **Preference sliders** – Recency vs popularity, friends vs global, topic weights; send to backend on change.
- [ ] **Profiles + engagement** – User profile page, follow button, like/repost actions calling backend.
- [ ] **Explainability** – Show why each tweet appears (source, score breakdown) from `ranking_explanation`.

## Current status

- **Backend**: Runs; `/health`, `/api/feed/{user_id}`, `/api/users`, `/api/engage` work. Seed data loads on startup. Preferences and follow/unfollow not persisted; no create-post or trends yet.
- **Frontend**: Not started (`frontend/` does not exist).
