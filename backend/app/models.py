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
    is_live: bool = True


class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    default_model: str


class GuardRuleInfo(BaseModel):
    id: str
    name: str
    category: str
    pattern: str
    match_type: str
    severity: str = "block"
    scope: str = "input"
    description: str


class GuardRulesResponse(BaseModel):
    count: int
    rules: List[GuardRuleInfo]


class GuardScanRequest(BaseModel):
    text: str
    scope: str = "input"


class GuardRuleHit(BaseModel):
    rule_id: str
    name: str
    category: str
    pattern: str
    match_type: str
    severity: str = "block"
    scope: str = "input"
    description: str


class GuardScanResponse(BaseModel):
    allowed: bool
    decision: str
    matched_rule_ids: List[str]
    hits: List[GuardRuleHit]
    ml_enabled: bool = False
    ml_loaded: bool = False
    ml_score: Optional[float] = None
    ml_label: Optional[str] = None


class ProviderStat(BaseModel):
    provider: str
    count: int
    avg_latency_ms: Optional[float] = None


class RequestLogEntry(BaseModel):
    request_id: str
    created_at: str
    prompt_excerpt: str
    provider: str
    model_name: str
    decision: str
    rule_hits: List[str]
    rule_hit_count: int
    latency_ms: float
    final_outcome: str
    score: float
    run_id: Optional[str] = None
    trace_id: str = ""
    phase: str = "complete"


class LogsListResponse(BaseModel):
    count: int
    limit: int
    offset: int
    logs: List[RequestLogEntry]


class StatsResponse(BaseModel):
    dataset_count: int
    run_count: int
    latest_pass_rate: Optional[float] = None
    latest_average_score: Optional[float] = None
    latest_run_at: Optional[str] = None
    total_requests: int = 0
    pass_count: int = 0
    fail_count: int = 0
    block_count: int = 0
    warn_count: int = 0
    request_pass_rate: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    by_provider: List[ProviderStat] = []


class EvalRunRequest(BaseModel):
    dataset_name: str
    prompt_template: str = Field(
        default="Answer the question briefly.\n\nQuestion: {input}\nAnswer:",
        description="Use {input} as a placeholder for each test case input.",
    )
    model_name: str = "gemini-2.5-flash-lite"


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