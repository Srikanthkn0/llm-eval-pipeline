from fastapi import APIRouter

from app.config import settings
from app.database import check_db
from app.models import HealthResponse
from app.services.llm_client import provider_status

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
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