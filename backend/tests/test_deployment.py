from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_cors_allows_configured_frontend_origin():
    origin = settings.FRONTEND_ORIGINS[0]
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin


def test_cors_allows_api_preflight():
    origin = settings.FRONTEND_ORIGINS[0]
    response = client.options(
        "/api/models",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_mock_allowed_without_keys_in_production():
    with patch("app.providers.registry.settings") as mock_settings:
        mock_settings.mock_allowed = True
        mock_settings.GEMINI_API_KEY = ""
        mock_settings.GROQ_API_KEY = ""
        mock_settings.OPENAI_API_KEY = ""

        from app.providers.registry import list_available_models

        models = list_available_models()
        assert any(model["id"] == "mock-model-v1" for model in models)


def test_health_reports_llm_provider_flags():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert "llm_providers" in payload
    assert "mock_allowed" in payload["llm_providers"]
    assert payload["status"] in {"ok", "degraded"}