import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "sample_data" / "sample_eval.csv"

client = TestClient(app)


def _wait_for_job(job_id: str, timeout_sec: float = 10.0):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        response = client.get(f"/api/evals/jobs/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(0.1)
    raise AssertionError(f"Job {job_id} did not complete in time")


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"ok", "degraded"}
    assert data["database"] == "connected"


def test_models_endpoint_includes_mock():
    response = client.get("/api/models")
    assert response.status_code == 200
    models = response.json()["models"]
    assert any(model["id"] == "mock-model-v1" for model in models)


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


def test_delete_dataset():
    with SAMPLE_CSV.open("rb") as handle:
        client.post(
            "/api/datasets/upload",
            files={"file": ("sample_eval.csv", handle, "text/csv")},
            data={"name": "delete-me"},
        )

    response = client.delete("/api/datasets/delete-me")
    assert response.status_code == 200

    list_response = client.get("/api/datasets")
    names = [item["name"] for item in list_response.json()["datasets"]]
    assert "delete-me" not in names


def test_run_eval_job_and_fetch_results():
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
    job = run_response.json()
    assert job["status"] in {"queued", "running", "completed"}

    finished = _wait_for_job(job["job_id"])
    assert finished["status"] == "completed"
    assert finished["run_id"]

    detail_response = client.get(f"/api/evals/runs/{finished['run_id']}")
    assert detail_response.status_code == 200
    run = detail_response.json()
    assert run["total_cases"] == 5
    assert run["passed_cases"] == 5
    assert run["pass_rate"] == 1.0


def test_stats_endpoint():
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert "dataset_count" in response.json()