from fastapi import APIRouter

from app.config import settings
from app.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
    )
