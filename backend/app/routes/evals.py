from fastapi import APIRouter

from app.models import EvalRunListResponse, EvalRunRequest, EvalRunResponse
from app.services.eval_runner import run_evaluation
from app.services.result_storage import list_runs, load_run

router = APIRouter()


@router.post("/evals/run", response_model=EvalRunResponse)
async def run_eval(payload: EvalRunRequest):
    return await run_evaluation(
        dataset_name=payload.dataset_name,
        prompt_template=payload.prompt_template,
        model_name=payload.model_name,
    )


@router.get("/evals/runs", response_model=EvalRunListResponse)
async def get_eval_runs():
    return EvalRunListResponse(runs=list_runs())


@router.get("/evals/runs/{run_id}", response_model=EvalRunResponse)
async def get_eval_run(run_id: str):
    return load_run(run_id)
