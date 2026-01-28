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

## Push to GitHub (this project only – no Taxora)

This repo must contain **only** the Personalized-X-Recommendation-Algorithm project. Do not run git from your home directory or from a folder that contains Taxora or other repos.

**To fix the repo** (if Taxora or other content was pushed by mistake) and push only this project:

1. Open your **system terminal** (Terminal.app, not Cursor’s).
2. Go only into this project folder:
   ```bash
   cd "/Users/hamzakhan/ Personalized-X-Recommendation-Algorithm"
   ```
3. Run:
   ```bash
   chmod +x push_to_github.sh
   ./push_to_github.sh
   ```
4. When asked, type `y` to **force-push**. This **replaces** whatever is on GitHub with only this project’s files (backend, README, etc.). No Taxora.

**Manual fix** (same idea – run only from this project folder):

```bash
cd "/Users/hamzakhan/ Personalized-X-Recommendation-Algorithm"
rm -rf .git
git init
git branch -M main
git add .
git commit -m "Personalized X Recommendation Algorithm only"
git remote add origin https://github.com/Hamzakhan7473/Personalized-X-Recommendation-Algorithm.git
git push -u origin main --force
```

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
