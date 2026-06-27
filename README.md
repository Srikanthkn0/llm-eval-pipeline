# LLM Eval Pipeline

A small evaluation platform for testing prompts and models against CSV test suites. Upload cases, run async eval jobs against live LLMs, review per-case scores, and gate regressions in CI.

**Live:** https://llm-eval-pipeline.vercel.app  
**API:** https://llm-eval-pipeline-api.onrender.com

## What it does

1. **Datasets** — upload CSV files with `input` and `expected_output` columns
2. **Eval jobs** — run each row through a prompt template and score the model response
3. **Results** — pass rate, per-case breakdown, and run history stored in Postgres
4. **CI gate** — GitHub Actions runs the sample suite and fails if pass rate drops below 80%

## Architecture

```
Browser
   │
   ▼
Vercel (React) ──proxy /api, /health──► Render (FastAPI)
                                              │
                                              ├── Neon Postgres
                                              └── Gemini API
```

| Layer | Tech |
|-------|------|
| Backend | FastAPI, gunicorn, SQLite (local) / PostgreSQL (prod) |
| Frontend | React, Vite |
| LLM | Gemini (production on Render), Groq/OpenAI optional, mock for CI |
| CI | GitHub Actions + pass-rate gate |
| Deploy | Render + Vercel + Neon (free tier) |

## Local development

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install && cp .env.example .env
npm run dev
```

Open http://localhost:5173. The mock model (`mock-model-v1`) works without API keys.

## Production deploy

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for Render, Vercel, Neon, and Gemini setup.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | System status and provider config |
| GET | `/api/models` | Available models |
| GET | `/api/stats` | Dashboard aggregates |
| POST | `/api/datasets/upload` | Upload CSV (`replace=true` to overwrite) |
| DELETE | `/api/datasets/{name}` | Delete dataset |
| POST | `/api/evals/run` | Start eval job → `job_id` |
| GET | `/api/evals/jobs/{id}` | Poll job progress |
| GET | `/api/evals/runs` | List past runs |
| GET | `/api/evals/runs/{id}` | Full run with per-case results |

Interactive docs: https://llm-eval-pipeline-api.onrender.com/docs

## CI

On every push to `main`, GitHub Actions:

1. Runs backend unit + API tests (`pytest`)
2. Executes eval against `sample_eval.csv` with the mock model
3. Fails the build if pass rate &lt; 80%

## Project notes

- **Scoring:** exact match, normalized text match, and keyword overlap (0.8 threshold)
- **Async jobs:** evals run in background tasks with progress polling — suited for slow LLM APIs
- **Render free tier:** API sleeps after ~15 min idle; first request may take 30–60s to wake

## License

MIT — see [LICENSE](LICENSE).