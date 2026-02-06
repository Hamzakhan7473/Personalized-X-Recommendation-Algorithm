# Personalized X Recommendation Algorithm

A **tunable, inspectable, and user-programmable** reimplementation of X’s “For You” feed ranking pipeline for research and experimentation. The system exposes the full ranking pipeline so that timelines, trends, and virality can be studied under different algorithmic preferences.

## Overview

This project reimplements core components of the [X (Twitter) For You feed algorithm](https://github.com/xai-org/x-algorithm) open-sourced by xAI. It combines:

- **End-to-end ranking pipeline**: candidate generation → hydration → filtering → scoring → selection, aligned with the [candidate generation → scoring → re-ranking](https://developers.google.com/machine-learning/recommendation/overview/types) paradigm used in large-scale recommendation systems.
- **Preference-driven personalization**: explicit controls over recency vs popularity, in-network vs out-of-network mix, diversity vs virality, and topic weights (tech, politics, culture, memes, finance).
- **Explainability**: each item in the feed is annotated with *why* it was ranked (source, action-score contributions, diversity penalty, recency/topic boosts), supporting auditability and discourse analysis.

The goal is to enable research on how algorithmic choices affect feed composition, filter bubbles, and emergent discourse—without relying on proprietary systems.

## Related Work & References

- **xai-org/x-algorithm** — [Algorithm powering the For You feed on X](https://github.com/xai-org/x-algorithm): Home Mixer orchestration, Thunder (in-network) and Phoenix (out-of-network retrieval + Grok-based ranking), candidate pipeline traits, multi-action prediction.
- **Hamzakhan7473/x-algorithm** — [Fork of x-algorithm](https://github.com/Hamzakhan7473/x-algorithm) (reference implementation; Rust/Python).
- **Google ML Recommendation Systems** — [Recommendation systems overview](https://developers.google.com/machine-learning/recommendation/overview/types): candidate generation, scoring, and re-ranking as the standard three-stage architecture.
- **DeepWiki x-algorithm** — [xai-org/x-algorithm on DeepWiki](https://deepwiki.com/xai-org/x-algorithm): detailed architecture, Candidate Pipeline traits (Source, Hydrator, Filter, Scorer, Selector), request processing flow, Phoenix/Thunder components, and scoring mechanism.

## Layered architecture

High-level layers: **User** → **Frontend (Next.js)** → **API (FastAPI)** → **Application logic** → **Ranking pipeline** (candidates → filter → score → diversity re-rank → top-K → explanations) → **Data layer** (in-memory store + SQLite) and optional **external services** (LLM, News API).

![Layered architecture – social feed app](docs/layered-architecture.jpg)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  FOR YOU FEED REQUEST                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  HOME MIXER (Orchestration)                                      │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐  │
│  │ Query Hydration │  │ User prefs, engagement history        │  │
│  └────────┬────────┘  └─────────────────────────────────────┘  │
│           ▼                                                       │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐  │
│  │ Thunder Source  │  │ Phoenix-style Retrieval (OON)         │  │
│  │ In-Network      │  │ Out-of-Network candidates             │  │
│  └────────┬────────┘  └────────────────┬────────────────────┘  │
│           └──────────────┬──────────────┘                       │
│                          ▼                                       │
│  Hydration → Pre-Scoring Filters → Scoring (tunable weights)      │
│  → Author Diversity → Selection → Post-Selection Filters        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RANKED FEED + EXPLAINABILITY (per-item attribution)            │
└─────────────────────────────────────────────────────────────────┘
```

- **Thunder-style source**: in-network posts from accounts the user follows (recent, per-author).
- **Phoenix-style source**: out-of-network candidates from a global corpus; mix controlled by a *friends vs global* parameter.
- **Scoring**: weighted combination of heuristic “action” scores (like, repost, reply, click, not_interested, etc.) with recency decay, topic weights, and in-network boost. Author-diversity attenuation reduces same-author stacking.
- **Explainability**: per-item `RankingExplanation` with final score, rank, source (in_network / out_of_network), action-score breakdown, diversity penalty, recency/topic boosts.

**Alignment with the three-stage recommendation architecture** ([Google ML: Recommendation systems overview](https://developers.google.com/machine-learning/recommendation/overview/types)):

| Stage | In this project |
|-------|-----------------|
| **Candidate generation** | Thunder (in-network) + Phoenix-style (out-of-network) sources; pre-scoring filters narrow to eligible candidates. |
| **Scoring** | Weighted scorer (action probabilities) + author-diversity scorer; assigns relevance scores to candidates. |
| **Re-ranking** | Selection (top K by score) + post-selection filters; final ordering and diversity/freshness. |

## Tunable Parameters (Research Controls)

| Parameter | Role |
|-----------|------|
| **Recency vs popularity** | Trade-off between time decay and engagement-based signals. |
| **Friends vs global** | Balance of in-network vs out-of-network candidates. |
| **Niche vs viral** | Diversity and author caps vs raw engagement. |
| **Topic weights** | Relative weight of tech, politics, culture, memes, finance. |
| **Diversity strength** | Penalty for repeated authors to limit filter bubbles. |
| **Exploration** | Degree of out-of-distribution or exploratory content. |
| **Negative signal strength** | Down-ranking of not_interested / block / mute / report. |

These controls allow experiments on how algorithmic preferences shift feed composition and emergent discourse.

## Design Decisions

1. **Composable pipeline** — Sources, filters, and scorers are separate stages; new signals or filters can be added for ablation studies.
2. **Multi-action scoring** — Multiple engagement types (positive and negative) are combined with configurable weights instead of a single relevance score.
3. **Author diversity** — Explicit diversity scorer to attenuate same-author runs and study saturation effects.
4. **Explainability by design** — Every ranked item carries an explanation (source, scores, penalties/boosts) for reproducibility and auditability.

## No API keys required (core)

**The project runs fully offline by default.** You do **not** need any API keys for the ranking pipeline or seed data. The feed uses heuristic scoring (no external ML APIs).

## Real-time LLM (optional: OpenAI or Gemini)

To enable **real-time generated posts and replies** (e.g. synthetic personas posting and replying as you use the app), set one of:

- **OpenAI**: `OPENAI_API_KEY` (optional: `OPENAI_MODEL`, default `gpt-4o-mini`)
- **Gemini**: `GEMINI_API_KEY` (optional: `GEMINI_MODEL`, default `gemini-2.5-flash`)

Example (backend directory):

```bash
export OPENAI_API_KEY=sk-...
# or
export GEMINI_API_KEY=...
uvicorn main:app --reload
```

When a key is set:

- **`GET /api/llm/status`** — returns `{ "available": true }` so the frontend can show LLM controls.
- **`POST /api/llm/generate-post`** — body: `{ "user_id": "u1", "publish": true }`. Generates a tweet as that user; if `publish` is true, the post is created and appears in feeds immediately (real-time update).
- **`POST /api/llm/generate-reply`** — body: `{ "user_id": "u2", "post_id": "p_..." }`. Returns generated reply text (no auto-publish).

Generated text is sanitized (max 280 chars, no leaked secrets). **Guardrails:** output is trimmed to 280 characters and blocklisted patterns (e.g. API keys, passwords) are redacted; you can extend the blocklist in `backend/llm_provider.py`. The backend prefers OpenAI if `OPENAI_API_KEY` is set, otherwise Gemini.

**LangChain (optional):** Install `langchain-core`, `langchain-openai`, and `langchain-google-genai` (see `requirements.txt`), then set `USE_LANGCHAIN=1` in the environment. Post and reply generation will use LangChain’s `ChatOpenAI` / `ChatGoogleGenerativeAI` instead of the raw APIs, so you can later add chains, agents, or tools on top of the same flow.

**Optional LLM seed:** On first run only, set `USE_LLM_SEED=1` (and an API key) to have the seed step generate extra posts and reply threads from each persona via the LLM, so the synthetic network starts with more varied, persona-driven content.

## Realtime news and tweets (optional)

You can inject **real-time headlines and (optionally) tweets** into the For You feed by setting API keys. External items are merged with in-network and out-of-network candidates and go through the same ranking pipeline.

### News API (headlines)

- **Get a key:** [NewsAPI.org](https://newsapi.org/) — free tier: 100 requests/day, top headlines.
- **Backend:** Set `NEWS_API_KEY` in the environment (or in `backend/.env`).
- **Optional:** `NEWS_API_COUNTRY` (e.g. `us`, default `us`), `NEWS_API_CATEGORY` (e.g. `technology`, `business`, `general`).

When set, the feed pipeline fetches top headlines and maps them to posts (source label “News”, topic from category). They are scored and ranked with the rest of the feed.

### Twitter / X (stub)

- **X API v2** requires [developer access](https://developer.twitter.com/) (Bearer token). Rate limits and approval apply.
- **Backend:** A stub is in `backend/ranking/realtime_sources.py` (`twitter_source_stub`). To add real tweets: set `TWITTER_BEARER_TOKEN` and implement a call to `GET /2/tweets/search/recent` (or similar), then map responses to `Candidate` (see docstring in `realtime_sources.py`).

### Flow

1. **get_candidates()** in `ranking/sources.py` merges Thunder (in-network), Phoenix (OON), and **get_realtime_candidates()** (news + optional Twitter).
2. Realtime items use synthetic posts and authors (e.g. “News” or source name); they are not stored in SQLite, only injected as candidates.
3. Scoring and explainability apply to realtime items the same way (source appears as out-of-network in “why this post”).

## Balancing engagement with diversity

The ranking pipeline is designed to reduce filter bubbles and popularity feedback loops:

- **Diversity strength** — The author-diversity scorer applies a penalty when the same author appears repeatedly in the candidate list, so the feed does not collapse to a single voice even if that author has high engagement.
- **Exploration** — The out-of-network (Phoenix-style) source and the *friends vs global* slider inject content from accounts the user does not follow; increasing this parameter increases exploration and reduces in-group saturation.
- **Recency vs popularity** — Lower *recency vs popularity* favors newer posts over raw like/repost counts, so the feed stays fresh and is less dominated by a few viral items.
- **Topic weights** — Adjusting tech/politics/culture/memes/finance weights shifts which topics surface; this allows studying how algorithmic emphasis shifts the *perceived* discourse (e.g. more tech vs more politics).

Together, these controls let you study how tuning the algorithm changes feed composition and emergent discourse patterns.

## Auditability & explainability

Every item in the ranked feed can be annotated with a **ranking explanation** (enable “Show why this post” in the UI):

- **Source** — Whether the post came from *Following* (in-network) or *For you* (out-of-network).
- **Rank & score** — Position in the ranked list and the final score used for ordering.
- **Diversity penalty** — How much the author-diversity term reduced the score (if the same author appeared recently).
- **Recency boost** — Contribution from post age.
- **Topic boost** — Contribution from topic weights.

The **explain/feed** API (`GET /api/explain/feed/{user_id}`) returns the full feed with these explanations. This supports reproducibility and research: you can record how a given set of preferences and engagement history produced a specific ordering, and reason about how changing weights would shift which posts appear and in what order. See **[docs/DIVERSITY_AND_EXPLAINABILITY.md](docs/DIVERSITY_AND_EXPLAINABILITY.md)** for more on diversity, exploration, and explainability.

## Repository structure

```
├── backend/          # Ranking engine (FastAPI), pipeline, store, seed data
│   ├── ranking/      # Home Mixer, sources, filters, scorers
│   ├── schemas.py    # Posts, users, preferences, RankingExplanation
│   └── store.py      # In-memory Thunder-style recent-post index
├── docs/             # MAKING_IT_LIKE_X.md, DIVERSITY_AND_EXPLAINABILITY.md, REALTIME_FEEDS.md
├── frontend/         # Next.js feed UI, preference sliders, users, explainability
└── README.md
```

## Run the project (backend + frontend)

**Make it work (checklist):**

1. **Backend env** — In `backend/`, copy `.env.example` to `.env` and add keys (optional: `GEMINI_API_KEY` or `OPENAI_API_KEY` for LLM; `NEWS_API_KEY` for realtime headlines). Core app works with no keys.
2. **Frontend env** — In `frontend/`, ensure `.env.local` exists with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` (or copy from `.env.local.example`).
3. **Terminal 1 (backend):** `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
4. **Terminal 2 (frontend):** `cd frontend && npm install && npm run dev`
5. **Browser:** Open [http://localhost:3000](http://localhost:3000), sign in as `me` (or `alice_dev`, `bob_trades`, etc.).

**1. Backend** (terminal one):

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Server: [http://127.0.0.1:8000](http://127.0.0.1:8000). API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). Data is persisted in `backend/data/app.db` (SQLite). On first run, seed users and posts are created; on later runs, existing data is loaded.

**2. Frontend** (terminal two):

```bash
cd frontend
npm install
npm run dev
```

App: [http://localhost:3000](http://localhost:3000). You are prompted to **sign in** with a handle (e.g. `me`, `alice_dev`, `bob_trades`, `carol_news`, `dave_memes`, `eve_founder`). After login you get a session; the feed, preferences, and engagements are scoped to that user. You can **post** (compose box), **like/repost/reply**, **follow/unfollow** on People, and **tune the algorithm** with sliders. Data and preferences survive server restart.

**Optional:** If the API is not at `http://127.0.0.1:8000`, copy `frontend/.env.local.example` to `frontend/.env.local` and set `NEXT_PUBLIC_API_URL`.

**API summary:** `POST /api/auth/login`, `GET /api/auth/me` (Bearer token), `GET/POST /api/feed`, `GET/PUT /api/users/{id}/preferences`, `POST /api/posts`, `GET /api/trends`, `POST /api/users/{id}/follow` and `/unfollow`, `POST /api/engage`.

## License

MIT. Algorithm design inspired by [xai-org/x-algorithm](https://github.com/xai-org/x-algorithm) (Apache-2.0).
