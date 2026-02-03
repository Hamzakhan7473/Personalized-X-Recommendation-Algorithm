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
- **Google ML Recommendation Systems** — [Recommendation systems overview](https://developers.google.com/machine-learning/recommendation/overview/types): candidate generation, scoring, and re-ranking as the standard three-stage architecture.
- **DeepWiki x-algorithm** — [Architecture and component documentation](https://deepwiki.com/xai-org/x-algorithm): pipeline execution model, data flow, scorers, and external services.

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

## Repository Structure

```
├── backend/          # Ranking engine (FastAPI), pipeline, store, seed data
│   ├── ranking/      # Home Mixer, sources, filters, scorers
│   ├── schemas.py    # Posts, users, preferences, RankingExplanation
│   └── store.py      # In-memory + Thunder-style recent-post index
├── frontend/         # (Planned) Feed UI, profiles, preference sliders
└── README.md
```

## Reproduction

Backend (Python):

```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
```

- **API docs (OpenAPI/Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) when the server is running.
- **API:** `POST /api/feed` with `user_id` and optional `AlgorithmPreferences`; response includes ranked items and per-item `ranking_explanation`. Also: `GET /api/feed/{user_id}`, `GET/PUT /api/users/{user_id}/preferences`, `POST /api/posts`, `GET /api/trends`, `POST /api/users/{user_id}/follow` and `/unfollow`, `POST /api/engage`.

## License

MIT. Algorithm design inspired by [xai-org/x-algorithm](https://github.com/xai-org/x-algorithm) (Apache-2.0).
