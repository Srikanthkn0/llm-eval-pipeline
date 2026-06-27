# LLM Eval CI/CD Pipeline

Full-stack web app for running prompt evaluations against CSV test datasets. Upload cases, configure a prompt template and model, execute evals, inspect per-case metrics, and gate changes in GitHub Actions before they ship.

**Live demo:** https://llm-eval-pipeline.vercel.app  
**API:** https://llm-eval-pipeline-api.onrender.com

## What it does

- Upload CSV datasets (`input`, `expected_output`, optional `category`)
- Run evals with a `{input}` prompt template and model name
- Score outputs with exact match, normalized match, and keyword overlap
- Persist datasets and run history in SQLite
- Review pass rate, scores, and latency in a React dashboard
- Fail CI when pass rate drops below 80% on the sample eval suite

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python, FastAPI, SQLite |
| Frontend | React, Vite |
| CI | GitHub Actions (pytest + eval gate + frontend build) |
| Deploy | Render (API + persistent disk), Vercel (frontend) |

## Project layout

```
llm-eval-pipeline/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint
│   │   ├── database.py       # SQLite schema + connection
│   │   ├── config.py         # env vars
│   │   ├── models.py         # Pydantic schemas
│   │   ├── routes/           # API routers
│   │   └── services/         # eval runner, scoring, LLM client
│   ├── tests/                # unit + API integration tests
│   ├── scripts/run_ci_eval.py
│   └── requirements.txt
├── frontend/
│   └── src/pages/            # Dashboard, Datasets, Run Eval, Results
├── .github/workflows/ci.yml
├── render.yaml               # Render Blueprint (repo root)
└── DEPLOYMENT.md
```

## Local setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App: http://localhost:5173

On first startup the API seeds a `sample` dataset from `backend/sample_data/sample_eval.csv`.

## Models

| Model | Behavior |
|-------|----------|
| `mock-model-v1` | Deterministic demo model (no API key). Used for local dev and CI. |
| `gpt-4o-mini` | Real OpenAI inference when `OPENAI_API_KEY` is set on the backend. |

## API quick test

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/api/datasets/upload \
  -F "file=@backend/sample_data/sample_eval.csv" \
  -F "name=my-dataset"

curl -X POST http://localhost:8000/api/evals/run \
  -H "Content-Type: application/json" \
  -d '{"dataset_name":"my-dataset","prompt_template":"Question: {input}\nAnswer:","model_name":"mock-model-v1"}'

curl http://localhost:8000/api/evals/runs
```

## CI

GitHub Actions runs on push/PR to `main`:

1. Backend unit tests + API integration tests (`pytest`)
2. Sample eval script with 80% pass-rate gate
3. Frontend production build

## Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for Render + Vercel setup, env vars, and troubleshooting.

## Resume talking points

- Built a full-stack eval workflow: CSV ingestion → prompt execution → scoring → persisted history
- Added SQLite persistence with Render persistent disk for production durability
- Integrated GitHub Actions quality gate that blocks merges below a pass-rate threshold
- Deployed split-stack app (FastAPI on Render, React on Vercel) with CORS and env-based API routing