from fastapi import APIRouter, BackgroundTasks

from app.models import (
    EvalJobResponse,
    EvalRunListResponse,
    EvalRunRequest,
    EvalRunResponse,
    ModelListResponse,
)
from app.services.job_service import get_job, queue_job, run_job
from app.services.llm_client import list_available_models
from app.services.result_storage import list_runs, load_run

router = APIRouter()


@router.get("/models", response_model=ModelListResponse)
async def get_models():
    models = list_available_models()
    live = [m for m in models if m.get("is_live", True)]
    default_model = live[0]["id"] if live else (models[0]["id"] if models else "mock-model-v1")
    return ModelListResponse(models=models, default_model=default_model)


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