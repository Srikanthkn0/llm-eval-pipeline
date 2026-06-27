import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.config import DATABASE_PATH, settings

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    name TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_runs (
    run_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    prompt_template TEXT NOT NULL,
    model_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    total_cases INTEGER NOT NULL,
    passed_cases INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    average_score REAL NOT NULL,
    average_latency_ms REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_case_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    case_index INTEGER NOT NULL,
    input TEXT NOT NULL,
    expected TEXT NOT NULL,
    actual TEXT NOT NULL,
    score REAL NOT NULL,
    passed INTEGER NOT NULL,
    latency_ms REAL NOT NULL,
    category TEXT,
    FOREIGN KEY (run_id) REFERENCES eval_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS eval_jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    prompt_template TEXT NOT NULL,
    model_name TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL DEFAULT 0,
    run_id TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_eval_case_results_run_id
    ON eval_case_results(run_id);
CREATE INDEX IF NOT EXISTS idx_eval_jobs_status
    ON eval_jobs(status);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    name TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_runs (
    run_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    prompt_template TEXT NOT NULL,
    model_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    total_cases INTEGER NOT NULL,
    passed_cases INTEGER NOT NULL,
    pass_rate DOUBLE PRECISION NOT NULL,
    average_score DOUBLE PRECISION NOT NULL,
    average_latency_ms DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_case_results (
    id SERIAL PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES eval_runs(run_id) ON DELETE CASCADE,
    case_index INTEGER NOT NULL,
    input TEXT NOT NULL,
    expected TEXT NOT NULL,
    actual TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    passed BOOLEAN NOT NULL,
    latency_ms DOUBLE PRECISION NOT NULL,
    category TEXT
);

CREATE TABLE IF NOT EXISTS eval_jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    prompt_template TEXT NOT NULL,
    model_name TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL DEFAULT 0,
    run_id TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_eval_case_results_run_id
    ON eval_case_results(run_id);
CREATE INDEX IF NOT EXISTS idx_eval_jobs_status
    ON eval_jobs(status);
"""


def ph() -> str:
    return "%s" if settings.use_postgres else "?"


def init_db() -> None:
    if settings.use_postgres:
        import psycopg

        with psycopg.connect(settings.DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(POSTGRES_SCHEMA)
            conn.commit()
        return

    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(SQLITE_SCHEMA)
        conn.commit()


def check_db() -> bool:
    try:
        with get_connection() as conn:
            if settings.use_postgres:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            else:
                conn.execute("SELECT 1").fetchone()
        return True
    except Exception:
        return False


@contextmanager
def get_connection() -> Iterator[Any]:
    if settings.use_postgres:
        import psycopg

        conn = psycopg.connect(settings.DATABASE_URL)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return

    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(
    conn: Any,
    query: str,
    params: tuple[Any, ...] = (),
) -> Any:
    if settings.use_postgres:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur
    return conn.execute(query, params)


def fetchone(conn: Any, query: str, params: tuple[Any, ...] = ()) -> Any:
    if settings.use_postgres:
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            if row is None:
                return None
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, row))
    row = conn.execute(query, params).fetchone()
    return dict(row) if row else None


def fetchall(conn: Any, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    if settings.use_postgres:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            if not rows:
                return []
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
    return [dict(row) for row in conn.execute(query, params).fetchall()]