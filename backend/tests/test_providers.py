from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.providers.base import ProviderRequest
from app.providers.gemini_provider import build_gemini_provider
from app.providers.groq_provider import build_groq_provider
from app.providers.mock_provider import mock_provider
from app.providers.openai_provider import build_openai_provider
from app.providers.registry import complete, list_available_models, validate_model_choice


@pytest.mark.anyio
async def test_mock_provider_returns_consistent_shape():
    response = await mock_provider.complete(
        ProviderRequest(prompt="What is the capital of France?", model="mock-model-v1")
    )
    assert response.text == "Paris"
    assert response.provider == "mock"
    assert response.model == "mock-model-v1"
    assert response.latency_ms >= 0


@pytest.mark.anyio
async def test_mock_provider_eval_dataset_answers():
    cases = [
        ("What is 2 + 2?", "4"),
        ("Capital of France?", "Paris"),
        ("What color is the sky on a clear day?", "blue"),
        ("How many days are in a week?", "7"),
        ("What does HTTP stand for?", "Hypertext Transfer Protocol"),
    ]
    for prompt, expected in cases:
        response = await mock_provider.complete(ProviderRequest(prompt=prompt))
        assert response.text == expected


def test_validate_model_rejects_unknown():
    with pytest.raises(HTTPException) as exc:
        validate_model_choice("unknown-model")
    assert exc.value.status_code == 400
    assert "Unknown model" in exc.value.detail


def test_validate_model_rejects_missing_openai_key():
    with patch("app.providers.registry.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = ""
        with pytest.raises(HTTPException) as exc:
            validate_model_choice("gpt-4o-mini")
    assert exc.value.status_code == 400
    assert "OPENAI_API_KEY" in exc.value.detail


def test_list_available_models_includes_mock_in_development():
    models = list_available_models()
    assert any(model["id"] == "mock-model-v1" for model in models)


def test_openai_provider_not_configured_without_key():
    with patch("app.providers.openai_provider.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = ""
        provider = build_openai_provider()
    assert not provider.is_configured()


@pytest.mark.anyio
async def test_openai_provider_complete_shape():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_response.json.return_value = {
        "choices": [{"message": {"content": " hello "}}],
    }

    with patch("app.providers.openai_provider.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "sk-test"
        mock_settings.LLM_REQUEST_TIMEOUT_SEC = 60
        mock_settings.LLM_MAX_RETRIES = 0
        provider = build_openai_provider()

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None
            client.post = AsyncMock(return_value=mock_response)
            client_cls.return_value = client

            response = await provider.complete(
                ProviderRequest(prompt="Say hello", model="gpt-4o-mini")
            )

    assert response.text == "hello"
    assert response.provider == "openai"
    assert response.model == "gpt-4o-mini"
    assert response.latency_ms >= 0


@pytest.mark.anyio
async def test_complete_uses_registry_for_mock():
    response = await complete("Capital of France?", "mock-model-v1")
    assert response.text == "Paris"
    assert response.provider == "mock"


@pytest.mark.anyio
async def test_gemini_provider_complete_shape():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Paris"}]}}],
    }

    with patch("app.providers.gemini_provider.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = "gem-test"
        mock_settings.LLM_REQUEST_TIMEOUT_SEC = 60
        mock_settings.LLM_MAX_RETRIES = 0
        provider = build_gemini_provider()

        with patch("httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None
            client.post = AsyncMock(return_value=mock_response)
            client_cls.return_value = client

            response = await provider.complete(
                ProviderRequest(prompt="Capital of France?", model="gemini-2.5-flash-lite")
            )

    assert response.text == "Paris"
    assert response.provider == "gemini"
    assert response.model == "gemini-2.5-flash-lite"


def test_groq_provider_not_configured_without_key():
    with patch("app.providers.groq_provider.settings") as mock_settings:
        mock_settings.GROQ_API_KEY = ""
        provider = build_groq_provider()
    assert not provider.is_configured()