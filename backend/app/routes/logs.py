from fastapi import APIRouter, HTTPException

from app.models import LogsListResponse, RequestLogEntry, StatsResponse
from app.services.request_log_store import list_logs
from app.services.result_storage import get_stats

router = APIRouter()


@router.get("/logs", response_model=LogsListResponse)
async def get_logs(
    limit: int = 50,
    offset: int = 0,
    decision: str | None = None,
    provider: str | None = None,
    run_id: str | None = None,
):
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200.")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0.")
    if decision and decision not in {"pass", "fail", "block", "warn"}:
        raise HTTPException(
            status_code=400,
            detail="decision must be 'pass', 'fail', 'block', or 'warn'.",
        )

    payload = list_logs(
        limit=limit,
        offset=offset,
        decision=decision,
        provider=provider,
        run_id=run_id,
    )
    return LogsListResponse(
        count=payload["count"],
        limit=payload["limit"],
        offset=payload["offset"],
        logs=[RequestLogEntry(**entry) for entry in payload["logs"]],
    )


@router.get("/stats", response_model=StatsResponse)
async def get_dashboard_stats():
    return StatsResponse(**get_stats())