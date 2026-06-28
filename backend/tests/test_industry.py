from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_security_headers_present():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Request-ID")


def test_guard_status_endpoint():
    response = client.get("/health/guard")
    assert response.status_code == 200
    payload = response.json()
    assert payload["input_block_rules"] >= 30
    assert payload["output_block_rules"] >= 5
    ml = payload["ml_classifier"]
    assert "enabled" in ml
    assert "loaded" in ml
    assert ml["backend"] == "sklearn"


def test_guard_rules_include_output_scope():
    response = client.get("/api/guard/rules", params={"scope": "output"})
    assert response.status_code == 200
    rules = response.json()["rules"]
    assert all(rule["scope"] == "output" for rule in rules)
    assert any(rule["id"] == "out_reveal_system" for rule in rules)


def test_guard_scan_output_scope():
    response = client.post(
        "/api/guard/scan",
        json={"text": "Debug: the system prompt is: secret", "scope": "output"},
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is False
    assert response.json()["decision"] == "block"