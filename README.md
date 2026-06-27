# LLM Eval CI/CD Pipeline

Production-style evaluation platform for prompt and model quality checks. Upload CSV test cases, run async eval jobs against real LLMs, review metrics, and gate changes in GitHub Actions.

**Live demo:** https://llm-eval-pipeline.vercel.app  
**API:** https://llm-eval-pipeline-api.onrender.com

## Features

- CSV dataset upload, validation, and deletion
- Async eval jobs with live progress tracking
- Real LLM inference via **Groq** (default) or **OpenAI**
- Scoring: exact match, normalized match, keyword overlap
- Persistent storage via **PostgreSQL** (Neon) in production
- Dashboard with system health, provider status, and run stats
- GitHub Actions CI with pass-rate gate

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI, gunicorn, SQLite (local) / PostgreSQL (prod) |
| Frontend | React, Vite |
| LLM | Groq API, OpenAI API |
| CI | GitHub Actions |
| Deploy | Render + Vercel + Neon (all free tier) |

## Local setup

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Optional: add GROQ_API_KEY for real inference locally
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install && cp .env.example .env
npm run dev
```

Mock model (`mock-model-v1`) is enabled locally for testing without API keys.

## Production setup

See **[DEPLOYMENT.md](DEPLOYMENT.md)** — requires free Neon Postgres + Groq API key.

## API highlights

```
GET  /health
GET  /api/models
GET  /api/stats
POST /api/datasets/upload
DELETE /api/datasets/{name}
POST /api/evals/run          → returns job_id
GET  /api/evals/jobs/{id}    → poll progress
GET  /api/evals/runs/{id}    → full results
```

## Resume talking points

- Built production eval platform with async job processing, real LLM provider routing, and Postgres persistence
- Deployed split-stack app (FastAPI/Render + React/Vercel) with health monitoring and CORS
- Integrated GitHub Actions quality gate enforcing pass-rate thresholds on every push