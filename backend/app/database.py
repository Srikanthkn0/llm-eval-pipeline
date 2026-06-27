import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import DATABASE_PATH

SCHEMA = """
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

CREATE INDEX IF NOT EXISTS idx_eval_case_results_run_id
    ON eval_case_results(run_id);
"""


def init_db() -> None:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()