# Production Deployment Guide

Total cost: **₹0** with free tiers (Vercel + Render + Neon + Groq).

## Architecture

| Component | Service | Purpose |
|-----------|---------|---------|
| Frontend | Vercel | React dashboard |
| Backend API | Render (free) | FastAPI + gunicorn |
| Database | Neon (free Postgres) | Durable datasets + eval history |
| LLM inference | Google Gemini (free API key) | Real model responses on Render |

---

## 1. Database — Neon Postgres (required for production)

SQLite on Render free tier loses data on redeploy. Use Neon instead.

1. Sign up at [neon.tech](https://neon.tech)
2. Create a project → copy the **connection string**
3. It looks like: `postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`

---

## 2. LLM — Gemini API key (required for production on Render)

**Why not Groq?** Groq blocks many cloud/datacenter IPs (Cloudflare error 1010). Gemini works from Render.

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Create a free API key
3. Default production model: `gemini-2.0-flash`

Mock model is disabled in production unless you set `ALLOW_MOCK_MODEL=true`.

---

## 3. Backend — Render

1. [dashboard.render.com/blueprint/new](https://dashboard.render.com/blueprint/new?repo=https://github.com/Srikanthkn0/llm-eval-pipeline)
2. Connect GitHub repo → **Apply**
3. Set environment variables in Render dashboard:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Your Neon connection string |
| `GEMINI_API_KEY` | Your Google AI Studio API key |
| `FRONTEND_ORIGINS` | `https://llm-eval-pipeline.vercel.app` |
| `GROQ_API_KEY` | _(optional — often blocked on Render)_ |
| `OPENAI_API_KEY` | _(optional, for gpt-4o-mini)_ |

4. Wait for deploy → verify:
```bash
curl https://llm-eval-pipeline-api.onrender.com/health
```

Expected: `"status":"ok"`, `"database":"connected"`, `"gemini":true`

---

## 4. Frontend — Vercel

1. Import repo at [vercel.com](https://vercel.com), root: `frontend`
2. Environment variable:

| Key | Value |
|-----|-------|
| `VITE_API_BASE_URL` | `https://llm-eval-pipeline-api.onrender.com` |

3. Deploy → open https://llm-eval-pipeline.vercel.app

---

## 5. Smoke test

1. Dashboard shows **ok** status, Gemini **configured**
2. Datasets tab shows seeded `sample` dataset
3. Run eval with **Gemini 2.0 Flash** — progress bar advances
4. Results tab shows completed run with pass rate

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `status: degraded` on health | Add `GEMINI_API_KEY` on Render |
| `error code: 1010` from Groq | Use Gemini instead — Groq blocks cloud IPs |
| `database: unavailable` | Set valid `DATABASE_URL` from Neon |
| CORS errors | Match `FRONTEND_ORIGINS` to exact Vercel URL |
| Eval job fails instantly | Check Render logs; verify API key and dataset name |
| Cold start slow (~30s) | Render free tier spins down after inactivity |