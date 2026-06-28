from fastapi import APIRouter

from app.config import settings
from app.database import check_db
from app.models import HealthResponse
from app.services.guard.engine import list_rules
from app.services.guard.ml_classifier import classifier_status
from app.services.job_service import count_active_jobs
from app.services.llm_client import provider_status

router = APIRouter()


def _health_payload() -> HealthResponse:
    db_ok = check_db()
    providers = provider_status()
    llm_ready = (
        providers["gemini"]
        or providers["groq"]
        or providers["openai"]
        or providers["mock_allowed"]
    )
    status = "ok" if db_ok and llm_ready else "degraded"
    return HealthResponse(
        status=status,
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        database="connected" if db_ok else "unavailable",
        llm_providers=providers,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return _health_payload()


@router.get("/health/live")
async def liveness():
    return {"status": "alive"}


@router.get("/health/ready", response_model=HealthResponse)
async def readiness():
    payload = _health_payload()
    if payload.database != "connected":
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Database unavailable.")
    return payload


@router.get("/health/guard")
async def guard_status():
    input_rules = [r for r in list_rules("input") if r.severity == "block"]
    output_rules = [r for r in list_rules("output") if r.severity == "block"]
    return {
        "input_block_rules": len(input_rules),
        "output_block_rules": len(output_rules),
        "normalization": "NFKC + zero-width strip",
        "ml_classifier": classifier_status(),
        "active_jobs": count_active_jobs(),
        "api_key_required": settings.require_api_key,
    }