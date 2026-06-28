import uuid
from datetime import datetime, timezone
from typing import Callable

from app.config import settings
from app.models import EvalCaseResult, EvalRunResponse
from app.providers.registry import complete
from app.services.dataset_service import load_dataset
from app.services.llm_client import build_prompt, validate_model_choice
from app.services.request_log_store import record_request
from app.services.result_storage import save_run
from app.services.scorer import score_output_with_hits


def _compute_pass_rate(passed_cases: int, total_cases: int) -> float:
    if total_cases == 0:
        return 0.0
    return round(passed_cases / total_cases, 4)


def _validate_eval_bounds(prompt_template: str, row_count: int) -> None:
    if row_count > settings.MAX_EVAL_ROWS:
        raise ValueError(
            f"Dataset has {row_count} rows; max allowed is {settings.MAX_EVAL_ROWS}."
        )
    if len(prompt_template) > settings.MAX_PROMPT_CHARS:
        raise ValueError(
            f"Prompt template exceeds {settings.MAX_PROMPT_CHARS} characters."
        )


async def run_evaluation(
    dataset_name: str,
    prompt_template: str,
    model_name: str,
    progress_callback: Callable[[int, int], None] | None = None,
) -> EvalRunResponse:
    validate_model_choice(model_name)

    rows = load_dataset(dataset_name)
    total_cases = len(rows)
    _validate_eval_bounds(prompt_template, total_cases)
    results: list[EvalCaseResult] = []

    if progress_callback:
        progress_callback(0, total_cases)

    run_id = uuid.uuid4().hex[:12]

    for index, row in enumerate(rows, start=1):
        if len(row["input"]) > settings.MAX_PROMPT_CHARS:
            raise ValueError(
                f"Row {index} input exceeds {settings.MAX_PROMPT_CHARS} characters."
            )

        prompt = build_prompt(prompt_template, row["input"])
        if len(prompt) > settings.MAX_PROMPT_CHARS:
            raise ValueError(f"Built prompt for row {index} exceeds max length.")

        provider_response = await complete(prompt, model_name)
        actual = provider_response.text
        latency_ms = provider_response.latency_ms

        score, passed, rule_hits = score_output_with_hits(actual, row["expected_output"])
        decision = "pass" if passed else "fail"

        record_request(
            prompt=prompt,
            provider=provider_response.provider,
            model_name=model_name,
            decision=decision,
            rule_hits=rule_hits,
            latency_ms=latency_ms,
            final_outcome=actual,
            score=score,
            run_id=run_id,
            phase="complete",
        )

        results.append(
            EvalCaseResult(
                input=row["input"],
                expected=row["expected_output"],
                actual=actual,
                score=round(score, 4),
                passed=passed,
                latency_ms=round(latency_ms, 2),
                category=row.get("category") or None,
            )
        )

        if progress_callback:
            progress_callback(index, total_cases)

    passed_cases = sum(1 for result in results if result.passed)
    average_score = round(sum(result.score for result in results) / total_cases, 4)
    average_latency_ms = round(sum(result.latency_ms for result in results) / total_cases, 2)
    pass_rate = _compute_pass_rate(passed_cases, total_cases)

    response = EvalRunResponse(
        run_id=run_id,
        dataset_name=dataset_name,
        prompt_template=prompt_template,
        model_name=model_name,
        created_at=datetime.now(timezone.utc).isoformat(),
        total_cases=total_cases,
        passed_cases=passed_cases,
        pass_rate=pass_rate,
        average_score=average_score,
        average_latency_ms=average_latency_ms,
        results=results,
    )

    save_run(response)
    return response