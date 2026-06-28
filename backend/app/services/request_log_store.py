import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.database import execute, fetchall, fetchone, get_connection, ph
from app.middleware.request_context import get_request_id

PROMPT_EXCERPT_LEN = 120
OUTCOME_PREVIEW_LEN = 160


def _prompt_excerpt(prompt: str) -> str:
    text = prompt.strip().replace("\n", " ")
    if len(text) <= PROMPT_EXCERPT_LEN:
        return text
    return f"{text[:PROMPT_EXCERPT_LEN]}..."


def _outcome_preview(text: str) -> str:
    cleaned = text.strip().replace("\n", " ")
    if len(cleaned) <= OUTCOME_PREVIEW_LEN:
        return cleaned
    return f"{cleaned[:OUTCOME_PREVIEW_LEN]}..."


def _row_to_entry(row: dict[str, Any]) -> dict[str, Any]:
    rule_hits = json.loads(row["rule_hits_json"])
    return {
        "request_id": row["request_id"],
        "created_at": row["created_at"],
        "run_id": row["run_id"],
        "model_name": row["model_name"],
        "prompt_excerpt": row["prompt_excerpt"],
        "provider": row["provider"],
        "decision": row["decision"],
        "rule_hits": rule_hits,
        "rule_hit_count": len(rule_hits),
        "latency_ms": row["latency_ms"],
        "final_outcome": row["final_outcome"],
        "score": row["score"],
        "trace_id": row.get("trace_id") or "",
        "phase": row.get("phase") or "complete",
    }


def record_request(
    *,
    prompt: str,
    provider: str,
    model_name: str,
    decision: str,
    rule_hits: list[str],
    latency_ms: float,
    final_outcome: str,
    score: float,
    run_id: str | None = None,
    request_id: str | None = None,
    phase: str = "complete",
) -> str:
    log_id = request_id or uuid.uuid4().hex[:12]
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        execute(
            conn,
            f"""
            INSERT INTO request_logs (
                request_id, created_at, run_id, model_name, prompt_excerpt,
                provider, decision, rule_hits_json, latency_ms, final_outcome, score,
                trace_id, phase
            ) VALUES ({ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()})
            """,
            (
                log_id,
                created_at,
                run_id,
                model_name,
                _prompt_excerpt(prompt),
                provider,
                decision,
                json.dumps(rule_hits),
                round(latency_ms, 2),
                _outcome_preview(final_outcome),
                round(score, 4),
                get_request_id(),
                phase,
            ),
        )
    return log_id


def list_logs(
    *,
    limit: int = 50,
    offset: int = 0,
    decision: str | None = None,
    provider: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    clauses: list[str] = []
    params: list[Any] = []

    if decision:
        clauses.append(f"decision = {ph()}")
        params.append(decision)
    if provider:
        clauses.append(f"provider = {ph()}")
        params.append(provider)
    if run_id:
        clauses.append(f"run_id = {ph()}")
        params.append(run_id)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_connection() as conn:
        total_row = fetchone(
            conn,
            f"SELECT COUNT(*) AS count FROM request_logs {where_sql}",
            tuple(params),
        )
        rows = fetchall(
            conn,
            f"""
            SELECT * FROM request_logs
            {where_sql}
            ORDER BY created_at DESC
            LIMIT {ph()} OFFSET {ph()}
            """,
            (*params, limit, offset),
        )

    total = total_row["count"] if total_row else 0
    return {
        "count": total,
        "limit": limit,
        "offset": offset,
        "logs": [_row_to_entry(row) for row in rows],
    }


def get_request_stats() -> dict[str, Any]:
    with get_connection() as conn:
        summary = fetchone(
            conn,
            """
            SELECT
                COUNT(*) AS total_requests,
                SUM(CASE WHEN decision = 'pass' THEN 1 ELSE 0 END) AS pass_count,
                SUM(CASE WHEN decision = 'fail' THEN 1 ELSE 0 END) AS fail_count,
                SUM(CASE WHEN decision = 'block' THEN 1 ELSE 0 END) AS block_count,
                SUM(CASE WHEN decision = 'warn' THEN 1 ELSE 0 END) AS warn_count,
                AVG(latency_ms) AS avg_latency_ms
            FROM request_logs
            """,
        )
        provider_rows = fetchall(
            conn,
            """
            SELECT
                provider,
                COUNT(*) AS count,
                AVG(latency_ms) AS avg_latency_ms
            FROM request_logs
            GROUP BY provider
            ORDER BY count DESC
            """,
        )

    total = summary["total_requests"] if summary else 0
    pass_count = summary["pass_count"] if summary else 0
    fail_count = summary["fail_count"] if summary else 0
    block_count = summary["block_count"] if summary else 0
    warn_count = summary["warn_count"] if summary else 0
    avg_latency = summary["avg_latency_ms"] if summary else None

    return {
        "total_requests": total or 0,
        "pass_count": pass_count or 0,
        "fail_count": fail_count or 0,
        "block_count": block_count or 0,
        "warn_count": warn_count or 0,
        "request_pass_rate": round(pass_count / total, 4) if total else None,
        "avg_latency_ms": round(avg_latency, 2) if avg_latency is not None else None,
        "by_provider": [
            {
                "provider": row["provider"],
                "count": row["count"],
                "avg_latency_ms": round(row["avg_latency_ms"], 2)
                if row["avg_latency_ms"] is not None
                else None,
            }
            for row in provider_rows
        ],
    }