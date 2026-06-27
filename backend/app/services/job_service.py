import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.database import execute, fetchone, get_connection, ph
from app.models import EvalJobResponse, EvalRunRequest
from app.services.eval_runner import run_evaluation
from app.services.llm_client import validate_model_choice


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(request: EvalRunRequest) -> EvalJobResponse:
    job_id = uuid.uuid4().hex[:12]
    now = _now()
    with get_connection() as conn:
        execute(
            conn,
            f"""
            INSERT INTO eval_jobs (
                job_id, status, dataset_name, prompt_template, model_name,
                progress, total, run_id, error, created_at, updated_at
            ) VALUES ({ph()}, {ph()}, {ph()}, {ph()}, {ph()}, 0, 0, NULL, NULL, {ph()}, {ph()})
            """,
            (
                job_id,
                "queued",
                request.dataset_name,
                request.prompt_template,
                request.model_name,
                now,
                now,
            ),
        )
    return EvalJobResponse(
        job_id=job_id,
        status="queued",
        dataset_name=request.dataset_name,
        model_name=request.model_name,
        progress=0,
        total=0,
        run_id=None,
        error=None,
        created_at=now,
        updated_at=now,
    )


def _update_job(
    job_id: str,
    *,
    status: str | None = None,
    progress: int | None = None,
    total: int | None = None,
    run_id: str | None = None,
    error: str | None = None,
) -> None:
    fields: list[str] = [f"updated_at = {ph()}"]
    values: list[object] = [_now()]

    if status is not None:
        fields.append(f"status = {ph()}")
        values.append(status)
    if progress is not None:
        fields.append(f"progress = {ph()}")
        values.append(progress)
    if total is not None:
        fields.append(f"total = {ph()}")
        values.append(total)
    if run_id is not None:
        fields.append(f"run_id = {ph()}")
        values.append(run_id)
    if error is not None:
        fields.append(f"error = {ph()}")
        values.append(error)

    values.append(job_id)
    query = f"UPDATE eval_jobs SET {', '.join(fields)} WHERE job_id = {ph()}"

    with get_connection() as conn:
        execute(conn, query, tuple(values))


def get_job(job_id: str) -> EvalJobResponse:
    with get_connection() as conn:
        row = fetchone(conn, f"SELECT * FROM eval_jobs WHERE job_id = {ph()}", (job_id,))
    if row is None:
        raise HTTPException(status_code=404, detail=f"Eval job '{job_id}' not found.")
    return EvalJobResponse(
        job_id=row["job_id"],
        status=row["status"],
        dataset_name=row["dataset_name"],
        model_name=row["model_name"],
        progress=row["progress"],
        total=row["total"],
        run_id=row["run_id"],
        error=row["error"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


async def run_job(job_id: str, request: EvalRunRequest) -> None:
    def on_progress(progress: int, total: int) -> None:
        _update_job(job_id, status="running", progress=progress, total=total)

    try:
        _update_job(job_id, status="running")
        result = await run_evaluation(
            dataset_name=request.dataset_name,
            prompt_template=request.prompt_template,
            model_name=request.model_name,
            progress_callback=on_progress,
        )
        _update_job(
            job_id,
            status="completed",
            progress=result.total_cases,
            total=result.total_cases,
            run_id=result.run_id,
        )
    except Exception as exc:
        _update_job(job_id, status="failed", error=str(exc))


def queue_job(request: EvalRunRequest) -> EvalJobResponse:
    validate_model_choice(request.model_name)
    return create_job(request)


async def run_job_and_wait(
    request: EvalRunRequest,
    *,
    poll_interval_sec: float = 0.5,
    timeout_sec: float = 120.0,
) -> EvalJobResponse:
    import asyncio

    validate_model_choice(request.model_name)
    job = create_job(request)
    await run_job(job.job_id, request)
    return get_job(job.job_id)