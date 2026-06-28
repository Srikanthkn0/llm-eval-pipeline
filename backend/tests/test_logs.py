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


def _run_sample_eval():
    with SAMPLE_CSV.open("rb") as handle:
        client.post(
            "/api/datasets/upload",
            files={"file": ("sample_eval.csv", handle, "text/csv")},
            data={"name": "log-test"},
        )

    run_response = client.post(
        "/api/evals/run",
        json={
            "dataset_name": "log-test",
            "prompt_template": "Question: {input}\nAnswer:",
            "model_name": "mock-model-v1",
        },
    )
    assert run_response.status_code == 200
    finished = _wait_for_job(run_response.json()["job_id"])
    assert finished["status"] == "completed"
    return finished["run_id"]


def test_logs_populated_after_eval():
    _run_sample_eval()

    response = client.get("/api/logs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 5
    assert len(payload["logs"]) >= 5

    entry = payload["logs"][0]
    assert entry["request_id"]
    assert entry["created_at"]
    assert entry["prompt_excerpt"]
    assert entry["provider"] == "mock"
    assert entry["decision"] in {"pass", "fail"}
    assert isinstance(entry["rule_hits"], list)
    assert entry["latency_ms"] >= 0
    assert entry["final_outcome"]


def test_logs_filter_by_decision():
    _run_sample_eval()

    passed = client.get("/api/logs", params={"decision": "pass"}).json()
    failed = client.get("/api/logs", params={"decision": "fail"}).json()

    assert all(log["decision"] == "pass" for log in passed["logs"])
    assert all(log["decision"] == "fail" for log in failed["logs"])


def test_logs_filter_by_provider():
    _run_sample_eval()

    payload = client.get("/api/logs", params={"provider": "mock"}).json()
    assert all(log["provider"] == "mock" for log in payload["logs"])


def test_stats_include_request_aggregates():
    _run_sample_eval()

    response = client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()

    assert stats["total_requests"] >= 5
    assert stats["pass_count"] >= 1
    assert stats["request_pass_rate"] is not None
    assert stats["avg_latency_ms"] is not None
    assert any(item["provider"] == "mock" for item in stats["by_provider"])


def test_logs_reject_invalid_decision_filter():
    response = client.get("/api/logs", params={"decision": "allow"})
    assert response.status_code == 400