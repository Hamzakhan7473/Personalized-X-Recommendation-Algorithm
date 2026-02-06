# Realtime news and tweets in the feed

The For You feed can include **real-time headlines** (and optionally **tweets**) from external APIs. These are merged with in-network and out-of-network candidates and ranked by the same pipeline.

## Env vars (backend)

| Variable | Purpose |
|----------|--------|
| `NEWS_API_KEY` | NewsAPI.org key; when set, top headlines are fetched and injected as candidates. |
| `NEWS_API_COUNTRY` | Optional 2-letter country (e.g. `us`, default `us`). |
| `NEWS_API_CATEGORY` | Optional: `business`, `entertainment`, `general`, `health`, `science`, `sports`, `technology`. |
| `TWITTER_BEARER_TOKEN` | Optional; stub in code. Set when you implement X API v2 fetch (see below). |

## News API

- **Sign up:** [NewsAPI.org](https://newsapi.org/) — free tier: 100 requests/day, top headlines.
- **Backend:** Set `NEWS_API_KEY` in `backend/.env` or your environment. Restart the backend.
- **Flow:** `get_candidates()` in `backend/ranking/sources.py` calls `get_realtime_candidates()`, which fetches from `https://newsapi.org/v2/top-headlines` and maps each article to a synthetic `Post` + `User` (source “News” or source name). They are scored and mixed with Thunder/Phoenix candidates.

## Twitter / X API (stub)

- **Access:** [developer.twitter.com](https://developer.twitter.com/) — X API v2 requires approval and has rate limits.
- **Backend:** `backend/ranking/realtime_sources.py` has `twitter_source_stub()`. To add real tweets:
  1. Set `TWITTER_BEARER_TOKEN`.
  2. Implement a request to `GET https://api.twitter.com/2/tweets/search/recent` (or another v2 endpoint) with query from user preferences/topics.
  3. Map each tweet to `Post` (id, author_id, text, created_at) and author to `User`.
  4. Return `list[Candidate]` with `source="out_of_network"`.
  5. Stub already returns an empty list when token is set until you implement the HTTP call.

## Architecture

- **Realtime candidates** are not persisted in SQLite; they are fetched on each feed request (or could be cached with TTL in a future change).
- **Ranking:** Same filters, weighted scorer, and diversity scorer apply. Realtime items use `source="out_of_network"` so they appear as “For you” in explainability.
- **Rate limits:** Respect News API (and Twitter) limits; consider caching or throttling if you have many users.

See README section **Realtime news and tweets (optional)** for a short summary.
