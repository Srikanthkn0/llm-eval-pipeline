from fastapi import APIRouter, BackgroundTasks

from app.models import (
    EvalJobResponse,
    EvalRunListResponse,
    EvalRunRequest,
    EvalRunResponse,
    ModelListResponse,
    StatsResponse,
)
from app.services.job_service import get_job, queue_job, run_job
from app.services.llm_client import list_available_models
from app.services.result_storage import get_stats, list_runs, load_run

router = APIRouter()


@router.get("/models", response_model=ModelListResponse)
async def get_models():
    models = list_available_models()
    default_model = "mock-model-v1"
    for candidate in ("gemini-2.0-flash", "gpt-4o-mini", "llama-3.1-8b-instant", "mock-model-v1"):
        if any(model["id"] == candidate and model["available"] for model in models):
            default_model = candidate
            break
    return ModelListResponse(models=models, default_model=default_model)


@router.get("/stats", response_model=StatsResponse)
async def get_dashboard_stats():
    stats = get_stats()
    return StatsResponse(**stats)


@router.post("/evals/run", response_model=EvalJobResponse)
async def run_eval(payload: EvalRunRequest, background_tasks: BackgroundTasks):
    job = queue_job(payload)
    background_tasks.add_task(run_job, job.job_id, payload)
    return job


@router.get("/evals/jobs/{job_id}", response_model=EvalJobResponse)
async def get_eval_job(job_id: str):
    return get_job(job_id)


@router.get("/evals/runs", response_model=EvalRunListResponse)
async def get_eval_runs():
    return EvalRunListResponse(runs=list_runs())


@router.get("/evals/runs/{run_id}", response_model=EvalRunResponse)
async def get_eval_run(run_id: str):
    return load_run(run_id)