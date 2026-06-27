# Production Deployment

Free-tier stack: Vercel + Render + Neon + Gemini API.

## Architecture

| Component | Service | Purpose |
|-----------|---------|---------|
| Frontend | Vercel | React dashboard (proxies API calls to Render) |
| Backend | Render | FastAPI + gunicorn |
| Database | Neon Postgres | Datasets and eval history |
| LLM | Google Gemini | Inference from Render (Groq blocked on many cloud IPs) |

---

## 1. Database — Neon Postgres

SQLite on Render loses data on redeploy. Use Neon instead.

1. Sign up at [neon.tech](https://neon.tech)
2. Create a project and copy the connection string
3. Format: `postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`

---

## 2. LLM — Gemini API key

Groq returns Cloudflare error 1010 from many datacenter IPs. Gemini works on Render.

1. Create a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Default models: `gemini-2.5-flash-lite` (fast) and `gemini-2.5-flash`
3. Mock model is disabled in production unless `ALLOW_MOCK_MODEL=true`

---

## 3. Backend — Render

1. Open [Render Blueprint](https://dashboard.render.com/blueprint/new?repo=https://github.com/Srikanthkn0/llm-eval-pipeline)
2. Connect the GitHub repo and apply
3. Set environment variables:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Neon connection string |
| `GEMINI_API_KEY` | Google AI Studio key |
| `FRONTEND_ORIGINS` | `https://llm-eval-pipeline.vercel.app` |
| `GROQ_API_KEY` | _(optional — often blocked on Render)_ |
| `OPENAI_API_KEY` | _(optional)_ |

4. Verify after deploy:

```bash
curl https://llm-eval-pipeline-api.onrender.com/health
```

Expected fields: `"status":"ok"`, `"database":"connected"`, `"llm_providers":{"gemini":true,...}`

---

## 4. Frontend — Vercel

1. Import the repo at [vercel.com](https://vercel.com) with root directory `frontend`
2. **No `VITE_API_BASE_URL` needed** — `vercel.json` proxies `/api` and `/health` to Render
3. Deploy → https://llm-eval-pipeline.vercel.app

Do not commit `frontend/.env` with localhost values. `.vercelignore` excludes it from CLI uploads.

---

## 5. Smoke test

1. Dashboard shows **ok** status and Gemini **configured**
2. Datasets tab lists the seeded `sample` dataset (5 rows)
3. Run eval with **Gemini 2.5 Flash-Lite** — progress bar advances
4. Results tab shows the completed run with pass rate and per-case table

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Backend unreachable on first load | Render free tier cold start — wait 30s and retry |
| `status: degraded` | Add `GEMINI_API_KEY` on Render |
| Groq error 1010 | Use Gemini instead |
| `database: unavailable` | Check `DATABASE_URL` from Neon |
| CORS errors | Match `FRONTEND_ORIGINS` to your Vercel URL |
| Eval fails instantly | Check Render logs; verify dataset name and API key |
| Frontend hits localhost | Redeploy without `frontend/.env` in the upload |