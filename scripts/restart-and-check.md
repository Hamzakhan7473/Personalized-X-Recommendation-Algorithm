# Restart everything and check

## 1. Stop any existing servers

In a terminal, stop anything on port 8000 (backend) and 3000 (frontend):

```bash
# macOS/Linux: find and kill process on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Same for port 3000 (frontend)
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
```

Or close the terminal windows where you ran `uvicorn` or `npm run dev` and use Ctrl+C.

---

## 2. Start backend

```bash
cd backend
pip install -r requirements.txt   # if you haven’t already
uvicorn main:app --reload
```

Leave this running. You should see:

- `Application startup complete.`
- `Uvicorn running on http://127.0.0.1:8000`

**Quick check:** Open http://127.0.0.1:8000/health → should show `{"status":"ok"}`.  
Open http://127.0.0.1:8000/docs → try **POST /api/auth/login** with body `{"handle": "me"}` → should return `user` and `session_id`.

---

## 3. Start frontend (new terminal)

```bash
cd frontend
npm install   # if you haven’t already
npm run dev
```

Leave this running. You should see:

- `Ready on http://localhost:3000`

**Quick check:** Open http://localhost:3000 → should redirect to **http://localhost:3000/login**. Sign in with handle **me** (or **alice_dev**, **bob_trades**, etc.) → should land on the feed. Post something, like a post, open People and follow someone — then refresh the page; data should still be there (persisted in `backend/data/app.db`).

---

## 4. Checklist

| Step | What to check |
|------|----------------|
| Backend | http://127.0.0.1:8000/health → `{"status":"ok"}` |
| Backend | http://127.0.0.1:8000/docs → POST /api/auth/login with `{"handle":"me"}` works |
| Frontend | http://localhost:3000 → redirects to /login |
| Frontend | Login with **me** → feed loads |
| Frontend | Compose a post → appears in feed |
| Frontend | Like / repost → counts update after refresh |
| Frontend | People → follow/unfollow → feed changes when you go back |
| Restart | Stop backend, start again → same data (SQLite) |

If anything fails, check that the **backend** is the one you just started (with auth and DB), not an old process still on port 8000.
