# Deployment Guide

Deploy the backend to **Render** and the frontend to **Vercel**. Total time: ~20 minutes.

## Prerequisites

- GitHub account with this repo pushed to `main`
- [Render](https://render.com) account (free tier works; persistent disk required for data)
- [Vercel](https://vercel.com) account

---

## 1. Push to GitHub

```bash
cd llm-eval-pipeline
git init
git add .
git commit -m "LLM eval pipeline: full-stack app with CI"
git branch -M main
git remote add origin https://github.com/Srikanthkn0/llm-eval-pipeline.git
git push -u origin main
```

Confirm GitHub Actions passes on the first push.

---

## 2. Deploy backend (Render)

### Option A: Blueprint (recommended)

1. Render Dashboard → **New** → **Blueprint**
2. Connect your GitHub repo
3. Render reads `render.yaml` at the **repo root** automatically
4. Set these env vars when prompted:
   - `FRONTEND_ORIGINS` → your Vercel URL (set after step 3, then update)
   - `OPENAI_API_KEY` → optional, for real OpenAI evals

### Option B: Manual web service

1. **New Web Service** → connect repo
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add a **persistent disk** (1 GB) mounted at `/var/data`
6. Environment variables:

| Key | Value |
|-----|-------|
| `APP_ENV` | `production` |
| `DATA_DIR` | `/var/data` |
| `FRONTEND_ORIGINS` | `https://your-app.vercel.app` |
| `OPENAI_API_KEY` | _(optional)_ |

7. Deploy and note your API URL: `https://llm-eval-pipeline-api.onrender.com`

### Verify backend

```bash
curl https://YOUR-RENDER-URL.onrender.com/health
curl https://YOUR-RENDER-URL.onrender.com/api/datasets
```

You should see the seeded `sample` dataset.

---

## 3. Deploy frontend (Vercel)

1. Vercel Dashboard → **Add New Project** → import repo
2. Root directory: `frontend`
3. Framework preset: **Vite**
4. Environment variable:

| Key | Value |
|-----|-------|
| `VITE_API_BASE_URL` | `https://YOUR-RENDER-URL.onrender.com` |

5. Deploy

`frontend/vercel.json` handles SPA routing.

### Verify frontend

1. Open your Vercel URL
2. Dashboard should show API status **ok**
3. Go to **Run eval** → run against `sample` with `mock-model-v1`
4. Check **Results** tab for the saved run

---

## 4. Fix CORS (if needed)

If the frontend shows CORS errors:

1. Render → your service → **Environment**
2. Set `FRONTEND_ORIGINS` to your exact Vercel URL (no trailing slash)
3. For preview deployments, use comma-separated origins:
   ```
   https://your-app.vercel.app,https://your-app-git-main.vercel.app
   ```
4. Redeploy the backend

---

## Environment variables reference

### Backend (`backend/.env` locally, Render in production)

| Variable | Required | Description |
|----------|----------|-------------|
| `FRONTEND_ORIGINS` | Yes | Comma-separated allowed CORS origins |
| `DATA_DIR` | Production | `/var/data` on Render (persistent disk) |
| `OPENAI_API_KEY` | No | Enables real OpenAI models |
| `APP_ENV` | No | `development` or `production` |

### Frontend (`frontend/.env` locally, Vercel env vars)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Yes | Render API URL (set before build) |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Dashboard says "API unreachable" | Check `VITE_API_BASE_URL` on Vercel; rebuild after changing |
| CORS error in browser console | Update `FRONTEND_ORIGINS` on Render to match Vercel URL exactly |
| Datasets disappear after redeploy | Ensure persistent disk is mounted at `/var/data` and `DATA_DIR=/var/data` |
| Render cold start is slow | Free tier spins down after inactivity; first request takes ~30s |
| CI fails on pass rate | Sample eval uses `mock-model-v1` + bundled CSV; should pass at 100% |
| OpenAI model fails | Set `OPENAI_API_KEY` on Render and redeploy |

---

## Post-deploy checklist

- [ ] `curl https://API_URL/health` returns `{"status":"ok"}`
- [ ] Vercel dashboard shows green API status
- [ ] Run eval on `sample` dataset succeeds
- [ ] Results appear in Results tab after refresh
- [ ] GitHub Actions CI is green on `main`
- [ ] Add live Vercel URL to README and resume