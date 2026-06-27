from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "sample_data" / "sample_eval.csv"

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_upload_and_list_dataset():
    with SAMPLE_CSV.open("rb") as handle:
        response = client.post(
            "/api/datasets/upload",
            files={"file": ("sample_eval.csv", handle, "text/csv")},
            data={"name": "api-test"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset"]["name"] == "api-test"
    assert payload["dataset"]["row_count"] == 5

    list_response = client.get("/api/datasets")
    assert list_response.status_code == 200
    names = [item["name"] for item in list_response.json()["datasets"]]
    assert "api-test" in names


def test_upload_rejects_invalid_csv():
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("bad.csv", b"wrong,columns\n1,2\n", "text/csv")},
        data={"name": "bad"},
    )
    assert response.status_code == 400
    assert "missing required columns" in response.json()["detail"].lower()


def test_upload_rejects_duplicate_dataset():
    with SAMPLE_CSV.open("rb") as handle:
        client.post(
            "/api/datasets/upload",
            files={"file": ("sample_eval.csv", handle, "text/csv")},
            data={"name": "dup-test"},
        )

    with SAMPLE_CSV.open("rb") as handle:
        response = client.post(
            "/api/datasets/upload",
            files={"file": ("sample_eval.csv", handle, "text/csv")},
            data={"name": "dup-test"},
        )

    assert response.status_code == 409


def test_run_eval_and_fetch_results():
    with SAMPLE_CSV.open("rb") as handle:
        client.post(
            "/api/datasets/upload",
            files={"file": ("sample_eval.csv", handle, "text/csv")},
            data={"name": "eval-flow"},
        )

    run_response = client.post(
        "/api/evals/run",
        json={
            "dataset_name": "eval-flow",
            "prompt_template": "Question: {input}\nAnswer:",
            "model_name": "mock-model-v1",
        },
    )
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["total_cases"] == 5
    assert run["passed_cases"] == 5
    assert run["pass_rate"] == 1.0
    assert len(run["results"]) == 5

    runs_response = client.get("/api/evals/runs")
    assert runs_response.status_code == 200
    run_ids = [item["run_id"] for item in runs_response.json()["runs"]]
    assert run["run_id"] in run_ids

    detail_response = client.get(f"/api/evals/runs/{run['run_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["run_id"] == run["run_id"]


def test_run_eval_missing_dataset():
    response = client.post(
        "/api/evals/run",
        json={"dataset_name": "missing", "model_name": "mock-model-v1"},
    )
    assert response.status_code == 404


def test_fetch_missing_run():
    response = client.get("/api/evals/runs/doesnotexist")
    assert response.status_code == 404