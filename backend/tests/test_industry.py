from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_security_headers_present():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Request-ID")


def test_service_status_endpoint():
    response = client.get("/health/status")
    assert response.status_code == 200
    payload = response.json()
    assert "active_jobs" in payload
    assert "api_key_required" in payload