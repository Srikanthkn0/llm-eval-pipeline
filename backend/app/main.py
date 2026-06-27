from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routes import datasets, evals, health
from app.services.dataset_service import list_datasets, save_dataset

SAMPLE_DATASET = (
    Path(__file__).resolve().parent.parent / "sample_data" / "sample_eval.csv"
)


def _seed_sample_dataset() -> None:
    if not SAMPLE_DATASET.exists():
        return
    if any(dataset.name == "sample" for dataset in list_datasets()):
        return
    save_dataset("sample", SAMPLE_DATASET.read_text(encoding="utf-8"), replace=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    _seed_sample_dataset()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(datasets.router, prefix="/api", tags=["datasets"])
app.include_router(evals.router, prefix="/api", tags=["evals"])


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )


@app.get("/")
async def root():
    return {
        "message": "LLM Eval Pipeline API",
        "docs": "/docs",
        "health": "/health",
    }