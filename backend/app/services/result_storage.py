from fastapi import HTTPException

from app.database import get_connection
from app.models import EvalCaseResult, EvalRunResponse, EvalRunSummary


def save_run(run: EvalRunResponse) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO eval_runs (
                run_id, dataset_name, prompt_template, model_name, created_at,
                total_cases, passed_cases, pass_rate, average_score, average_latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.run_id,
                run.dataset_name,
                run.prompt_template,
                run.model_name,
                run.created_at,
                run.total_cases,
                run.passed_cases,
                run.pass_rate,
                run.average_score,
                run.average_latency_ms,
            ),
        )
        conn.executemany(
            """
            INSERT INTO eval_case_results (
                run_id, case_index, input, expected, actual,
                score, passed, latency_ms, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run.run_id,
                    index,
                    case.input,
                    case.expected,
                    case.actual,
                    case.score,
                    int(case.passed),
                    case.latency_ms,
                    case.category,
                )
                for index, case in enumerate(run.results)
            ],
        )
        conn.commit()


def list_runs() -> list[EvalRunSummary]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT run_id, dataset_name, model_name, created_at,
                   total_cases, passed_cases, pass_rate,
                   average_score, average_latency_ms
            FROM eval_runs
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [
        EvalRunSummary(
            run_id=row["run_id"],
            dataset_name=row["dataset_name"],
            model_name=row["model_name"],
            created_at=row["created_at"],
            total_cases=row["total_cases"],
            passed_cases=row["passed_cases"],
            pass_rate=row["pass_rate"],
            average_score=row["average_score"],
            average_latency_ms=row["average_latency_ms"],
        )
        for row in rows
    ]


def load_run(run_id: str) -> EvalRunResponse:
    with get_connection() as conn:
        run_row = conn.execute(
            "SELECT * FROM eval_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if run_row is None:
            raise HTTPException(status_code=404, detail=f"Eval run '{run_id}' not found.")

        case_rows = conn.execute(
            """
            SELECT input, expected, actual, score, passed, latency_ms, category
            FROM eval_case_results
            WHERE run_id = ?
            ORDER BY case_index
            """,
            (run_id,),
        ).fetchall()

    return EvalRunResponse(
        run_id=run_row["run_id"],
        dataset_name=run_row["dataset_name"],
        prompt_template=run_row["prompt_template"],
        model_name=run_row["model_name"],
        created_at=run_row["created_at"],
        total_cases=run_row["total_cases"],
        passed_cases=run_row["passed_cases"],
        pass_rate=run_row["pass_rate"],
        average_score=run_row["average_score"],
        average_latency_ms=run_row["average_latency_ms"],
        results=[
            EvalCaseResult(
                input=row["input"],
                expected=row["expected"],
                actual=row["actual"],
                score=row["score"],
                passed=bool(row["passed"]),
                latency_ms=row["latency_ms"],
                category=row["category"],
            )
            for row in case_rows
        ],
    )