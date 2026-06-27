#!/usr/bin/env python3
"""
Run a sample eval against the bundled dataset. Used in CI to gate on pass rate.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("ALLOW_MOCK_MODEL", "true")

from app.database import init_db
from app.models import EvalRunRequest
from app.services.dataset_service import save_dataset
from app.services.job_service import run_job_and_wait

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "sample_data" / "sample_eval.csv"
DEFAULT_PROMPT = "Question: {input}\nAnswer:"


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run sample eval for CI")
    parser.add_argument("--min-pass-rate", type=float, default=0.8)
    parser.add_argument("--dataset-name", default="ci-sample")
    args = parser.parse_args()

    init_db()
    content = SAMPLE_CSV.read_text(encoding="utf-8")
    save_dataset(args.dataset_name, content, replace=True)

    request = EvalRunRequest(
        dataset_name=args.dataset_name,
        prompt_template=DEFAULT_PROMPT,
        model_name="mock-model-v1",
    )
    job = await run_job_and_wait(request)

    if job.status != "completed" or not job.run_id:
        print(f"FAILED: job ended with status={job.status} error={job.error}", file=sys.stderr)
        return 1

    from app.services.result_storage import load_run

    result = load_run(job.run_id)
    print(f"Run ID: {result.run_id}")
    print(f"Pass rate: {result.pass_rate:.2%} ({result.passed_cases}/{result.total_cases})")
    print(f"Avg score: {result.average_score:.2f}")
    print(f"Avg latency: {result.average_latency_ms:.0f} ms")

    if result.pass_rate < args.min_pass_rate:
        print(
            f"FAILED: pass rate {result.pass_rate:.2%} is below threshold {args.min_pass_rate:.2%}",
            file=sys.stderr,
        )
        return 1

    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))