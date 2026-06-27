import uuid
from datetime import datetime, timezone

from app.models import EvalCaseResult, EvalRunResponse
from app.services.dataset_service import load_dataset
from app.services.llm_client import build_prompt, generate_completion
from app.services.result_storage import save_run
from app.services.scorer import score_output


def _compute_pass_rate(passed_cases: int, total_cases: int) -> float:
    if total_cases == 0:
        return 0.0
    return round(passed_cases / total_cases, 4)


async def run_evaluation(
    dataset_name: str,
    prompt_template: str,
    model_name: str,
) -> EvalRunResponse:
    rows = load_dataset(dataset_name)
    results: list[EvalCaseResult] = []

    for row in rows:
        prompt = build_prompt(prompt_template, row["input"])
        actual, latency_ms = await generate_completion(prompt, model_name)
        score, passed = score_output(actual, row["expected_output"])

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

    total_cases = len(results)
    passed_cases = sum(1 for result in results if result.passed)
    average_score = round(sum(result.score for result in results) / total_cases, 4)
    average_latency_ms = round(sum(result.latency_ms for result in results) / total_cases, 2)
    pass_rate = _compute_pass_rate(passed_cases, total_cases)

    run_id = uuid.uuid4().hex[:12]
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
