import csv
import io
import re
from datetime import datetime, timezone

from fastapi import HTTPException

from app.database import get_connection
from app.models import DatasetInfo

REQUIRED_COLUMNS = {"input", "expected_output"}


def _sanitize_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    if not cleaned:
        raise HTTPException(status_code=400, detail="Dataset name is invalid after sanitization.")
    return cleaned


def _parse_csv(content: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty or missing a header row.")

    columns = {col.strip().lower() for col in reader.fieldnames if col}
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required columns: {', '.join(sorted(missing))}",
        )

    rows: list[dict[str, str]] = []
    for index, raw_row in enumerate(reader, start=2):
        row = {key.strip().lower(): (value or "").strip() for key, value in raw_row.items() if key}
        if not row.get("input") or not row.get("expected_output"):
            raise HTTPException(
                status_code=400,
                detail=f"Row {index} is missing input or expected_output.",
            )
        rows.append(
            {
                "input": row["input"],
                "expected_output": row["expected_output"],
                "category": row.get("category", ""),
            }
        )

    if not rows:
        raise HTTPException(status_code=400, detail="CSV has a header but no data rows.")

    return rows


def save_dataset(name: str, content: str, *, replace: bool = False) -> DatasetInfo:
    dataset_name = _sanitize_name(name)
    rows = _parse_csv(content)

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT name FROM datasets WHERE name = ?",
            (dataset_name,),
        ).fetchone()
        if existing and not replace:
            raise HTTPException(
                status_code=409,
                detail=f"Dataset '{dataset_name}' already exists. Choose a different name.",
            )

        created_at = datetime.now(timezone.utc).isoformat()
        if existing:
            conn.execute(
                """
                UPDATE datasets
                SET content = ?, row_count = ?, created_at = ?
                WHERE name = ?
                """,
                (content, len(rows), created_at, dataset_name),
            )
        else:
            conn.execute(
                """
                INSERT INTO datasets (name, content, row_count, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (dataset_name, content, len(rows), created_at),
            )
        conn.commit()

    return DatasetInfo(name=dataset_name, file_name=f"{dataset_name}.csv", row_count=len(rows))


def delete_dataset(name: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM datasets WHERE name = ?", (name,))
        conn.commit()
        return cursor.rowcount > 0


def list_datasets() -> list[DatasetInfo]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name, row_count FROM datasets ORDER BY name"
        ).fetchall()

    return [
        DatasetInfo(name=row["name"], file_name=f"{row['name']}.csv", row_count=row["row_count"])
        for row in rows
    ]


def load_dataset(name: str) -> list[dict[str, str]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT content FROM datasets WHERE name = ?",
            (name,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{name}' not found.")

    return _parse_csv(row["content"])