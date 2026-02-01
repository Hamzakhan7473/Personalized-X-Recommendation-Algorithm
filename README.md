# Personalized X Recommendation Algorithm

A **tunable, inspectable, and user-programmable** reimplementation of X’s “For You” ranking pipeline, inspired by [xai-org/x-algorithm](https://github.com/xai-org/x-algorithm). It combines:

- **End-to-end ranking pipeline** (candidate generation → hydration → filtering → scoring → selection)
- **Preference-driven personalization** (recency vs popularity, friends vs global, niche vs viral, topic weights)
- **Synthetic social network** with LLM-generated personas (founders, journalists, meme accounts, traders, politicians)
- **Full-stack web app** (feed, profiles, follow graph, likes, reposts, replies, trends, notifications) powered by the ranking engine

## Architecture (X-inspired)

```
┌─────────────────────────────────────────────────────────────────┐
│  FOR YOU FEED REQUEST                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  HOME MIXER (Orchestration)                                      │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐   │
│  │ Query Hydration │  │ User prefs, engagement history       │   │
│  └────────┬────────┘  └─────────────────────────────────────┘   │
│           ▼                                                       │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐   │
│  │ Thunder Source  │  │ Phoenix-style Retrieval (OON)        │   │
│  │ In-Network      │  │ Out-of-Network candidates            │   │
│  └────────┬────────┘  └────────────────┬────────────────────┘   │
│           └──────────────┬──────────────┘                        │
│                          ▼                                       │
│  Hydration → Pre-Scoring Filters → Scoring (tunable weights)      │
│  → Author Diversity → Selection → Post-Selection Filters         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RANKED FEED + EXPLAINABILITY (why each tweet appears)           │
└─────────────────────────────────────────────────────────────────┘
```

## Project structure

```
├── backend/          # FastAPI ranking engine, personas, API
├── frontend/         # Next.js app (feed, profiles, preference sliders)
├── shared/           # Shared types/schemas (optional)
└── README.md
```

## Branches

| Branch     | Use for                         |
|------------|----------------------------------|
| `main`     | Stable, merged code              |
| `backend`  | Backend work (FastAPI, ranking)  |
| `frontend` | Frontend work (Next.js, UI)      |

**Switch branch:**
```bash
git checkout backend
git checkout frontend
```

**Push a branch to GitHub** — run **one line at a time** (do not copy a line that has a comment on the same line):
```bash
git push -u origin backend
```
```bash
git push -u origin frontend
```

## Push to GitHub

Run these from **this project folder** in your terminal:

**Option 1 – script**
```bash
cd "/Users/hamzakhan/ Personalized-X-Recommendation-Algorithm"
chmod +x push_to_github.sh
./push_to_github.sh
```

**Option 2 – manual**
```bash
cd "/Users/hamzakhan/ Personalized-X-Recommendation-Algorithm"
git add .
git commit -m "Update"
git remote add origin https://github.com/Hamzakhan7473/Personalized-X-Recommendation-Algorithm.git
git push -u origin main
```
If the repo already has a remote, use `git push origin main` (or `git push origin backend` / `git push origin frontend` for those branches).

## Quick start

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Preference controls (user-programmable)

- **Recency vs popularity** – time decay vs like/repost counts
- **Friends vs global** – in-network vs out-of-network mix
- **Niche vs viral** – diversity and author caps vs raw engagement
- **Topic weights** – tech / politics / culture / memes / finance

## License

MIT (algorithm design inspired by xai-org/x-algorithm, Apache-2.0)
