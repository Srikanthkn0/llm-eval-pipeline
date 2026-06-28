# Deployment

Vercel (frontend) + Render (backend) + Neon (Postgres) + Gemini. All free tier.

- App: https://llm-eval-pipeline.vercel.app
- API: https://llm-eval-pipeline-api.onrender.com

```
Browser → Vercel → proxy /api,/health → Render → Neon
                                         └→ Gemini (or mock)
```

`vercel.json` sends API traffic to Render. The browser talks to one origin, so CORS only matters for direct API calls (e.g. curl, local frontend against prod API). Set `FRONTEND_ORIGINS` to your Vercel URL.

Don't use SQLite on Render — it resets on redeploy. Use Neon.

## Commands

**Render** (`backend/`):

```bash
pip install -r requirements.txt   # build
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 120   # start
```

In `render.yaml` already. Render sets `$PORT`.

**Vercel** (`frontend/`):

```bash
npm ci
npm run build    # output: dist/
```

Root directory: `frontend`. No start command.

**Local:**

```bash
cd backend && ./run.sh              # :8000
cd frontend && npm run dev            # :5173
```

## Env vars

### Render

| Var | Required | Notes |
|-----|----------|-------|
| `APP_ENV` | yes | `production` |
| `FRONTEND_ORIGINS` | yes | `https://llm-eval-pipeline.vercel.app,http://localhost:5173` |
| `DATABASE_URL` | yes | Neon URL, include `?sslmode=require` |
| `GEMINI_API_KEY` | for live LLM | Works on Render. Get one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `ALLOW_MOCK_MODEL` | recommended | `true` — keeps demo working without keys |
| `GROQ_API_KEY` | optional | Often blocked on cloud IPs (CF 1010) |
| `OPENAI_API_KEY` | optional | |

Copy from `backend/.env.example` for the rest (`LLM_REQUEST_TIMEOUT_SEC`, etc.).

### Vercel

Leave `VITE_API_BASE_URL` unset. The proxy handles it.

Don't upload `frontend/.env` with localhost — `.vercelignore` drops it, but clear it in the Vercel UI too if you set it once.

## Mock fallback

If prod has no provider keys, `mock-model-v1` turns on anyway. With `ALLOW_MOCK_MODEL=true` (default in `render.yaml`), mock is always available in prod.

Mock answers are fixed — the `sample` dataset passes 100%. For real evals, set `GEMINI_API_KEY` and pick Gemini in the UI.

Check: `GET /health` → `llm_providers.mock_allowed`.

## CORS

Origins come from `FRONTEND_ORIGINS` in `app/main.py`. No trailing slash on the Vercel URL. Wildcards don't work — add each preview URL manually if you need them.

```bash
curl -sI -X OPTIONS "https://llm-eval-pipeline-api.onrender.com/health" \
  -H "Origin: https://llm-eval-pipeline.vercel.app" \
  -H "Access-Control-Request-Method: GET" | grep -i access-control
```

Or: `pytest tests/test_deployment.py -v`

## Deploy

### 1. Neon

1. [neon.tech](https://neon.tech) → new project
2. Copy connection string

### 2. Render

Blueprint: [dashboard.render.com/blueprint/new](https://dashboard.render.com/blueprint/new?repo=https://github.com/Srikanthkn0/llm-eval-pipeline)

Set in Environment:
- `DATABASE_URL`
- `GEMINI_API_KEY`

Wait for Live, then:

```bash
curl -s https://llm-eval-pipeline-api.onrender.com/health | jq
```

Want `"status":"ok"` and `"database":"connected"`.

Manual setup: Web Service, root `backend`, same build/start as above.

### 3. Vercel

Import repo, root `frontend`, no env vars. If your URL isn't `llm-eval-pipeline.vercel.app`, update `FRONTEND_ORIGINS` on Render.

```bash
curl -s https://llm-eval-pipeline.vercel.app/health | jq .status
```

## Smoke test

Set `API=https://llm-eval-pipeline-api.onrender.com` and `APP=https://llm-eval-pipeline.vercel.app`.

1. `curl -s $API/health` — ok, db connected, gemini or mock_allowed
2. `curl -s $API/api/models` — at least one model
3. App → Datasets — `sample` exists
4. Run eval on `sample` (mock or Gemini) — job finishes
5. Results — pass rate + table
6. `curl -s "$API/api/logs?limit=5"` — count ≥ 5
7. `curl -s $APP/health` — same as step 1 via proxy

Cold start: if the dashboard errors, wait 30s and hit Retry.

## Files

- `render.yaml` — Render service
- `frontend/vercel.json` — build + proxy
- `backend/run.sh` — local server
- `backend/.env.example` — env template

## When things break

| Problem | Likely fix |
|---------|------------|
| Slow first load | Render cold start; wait and retry |
| `degraded` health | Add `GEMINI_API_KEY` or enable mock |
| Groq 1010 | Use Gemini on Render |
| `database: unavailable` | Check `DATABASE_URL` |
| CORS in browser | `FRONTEND_ORIGINS` must match Vercel URL exactly |
| Frontend calls localhost | Remove `VITE_API_BASE_URL` on Vercel; redeploy |
| Eval fails immediately | Render logs; wrong dataset name or missing model |