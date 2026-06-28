import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware.auth import ApiKeyMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.database import init_db
from app.routes import datasets, evals, health, logs
from app.services.dataset_service import list_datasets, save_dataset
from app.services.job_service import recover_stale_jobs

logger = logging.getLogger(__name__)

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
SEED_DATASETS = {
    "sample": SAMPLE_DIR / "sample_eval.csv",
    "general": SAMPLE_DIR / "general_eval.csv",
}


def _seed_datasets() -> None:
    existing = {dataset.name for dataset in list_datasets()}
    for name, path in SEED_DATASETS.items():
        if not path.exists() or name in existing:
            continue
        save_dataset(name, path.read_text(encoding="utf-8"), replace=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    _seed_datasets()
    recovered = recover_stale_jobs()
    if recovered:
        logger.warning("Marked %s stale eval job(s) as failed on startup.", recovered)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app.include_router(health.router, tags=["health"])
app.include_router(datasets.router, prefix="/api", tags=["datasets"])
app.include_router(evals.router, prefix="/api", tags=["evals"])
app.include_router(logs.router, prefix="/api", tags=["logs"])


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", _request.url.path)
    detail = (
        "Internal server error."
        if settings.is_production
        else f"Internal server error: {exc}"
    )
    return JSONResponse(status_code=500, content={"detail": detail})


@app.get("/")
async def root():
    return {
        "message": "LLM Eval Pipeline API",
        "docs": "/docs",
        "health": "/health",
    }