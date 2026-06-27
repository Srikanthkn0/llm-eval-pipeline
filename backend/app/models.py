from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    database: str
    llm_providers: dict[str, bool]


class DatasetInfo(BaseModel):
    name: str
    file_name: str
    row_count: int


class DatasetListResponse(BaseModel):
    datasets: List[DatasetInfo]


class DatasetUploadResponse(BaseModel):
    message: str
    dataset: DatasetInfo


class ModelInfo(BaseModel):
    id: str
    label: str
    provider: str
    available: bool


class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    default_model: str


class StatsResponse(BaseModel):
    dataset_count: int
    run_count: int
    latest_pass_rate: Optional[float] = None
    latest_average_score: Optional[float] = None
    latest_run_at: Optional[str] = None


class EvalRunRequest(BaseModel):
    dataset_name: str
    prompt_template: str = Field(
        default="Answer the question briefly.\n\nQuestion: {input}\nAnswer:",
        description="Use {input} as a placeholder for each test case input.",
    )
    model_name: str = "gemini-2.0-flash"


class EvalJobResponse(BaseModel):
    job_id: str
    status: str
    dataset_name: str
    model_name: str
    progress: int
    total: int
    run_id: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


class EvalCaseResult(BaseModel):
    input: str
    expected: str
    actual: str
    score: float
    passed: bool
    latency_ms: float
    category: Optional[str] = None


class EvalRunSummary(BaseModel):
    run_id: str
    dataset_name: str
    model_name: str
    created_at: str
    total_cases: int
    passed_cases: int
    pass_rate: float
    average_score: float
    average_latency_ms: float


class EvalRunListResponse(BaseModel):
    runs: List[EvalRunSummary]


class EvalRunResponse(BaseModel):
    run_id: str
    dataset_name: str
    prompt_template: str
    model_name: str
    created_at: str
    total_cases: int
    passed_cases: int
    pass_rate: float
    average_score: float
    average_latency_ms: float
    results: List[EvalCaseResult]