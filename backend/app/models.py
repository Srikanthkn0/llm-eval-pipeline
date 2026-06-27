from pydantic import BaseModel, Field
from typing import List, Optional


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str


class DatasetInfo(BaseModel):
    name: str
    file_name: str
    row_count: int


class DatasetListResponse(BaseModel):
    datasets: List[DatasetInfo]


class DatasetUploadResponse(BaseModel):
    message: str
    dataset: DatasetInfo


class EvalRunRequest(BaseModel):
    dataset_name: str
    prompt_template: str = Field(
        default="Answer the question briefly.\n\nQuestion: {input}\nAnswer:",
        description="Use {input} as a placeholder for each test case input.",
    )
    model_name: str = "mock-model-v1"


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
