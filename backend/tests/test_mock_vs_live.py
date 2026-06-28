import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers.base import ProviderRequest
from app.providers.mock_provider import mock_provider

client = TestClient(app)


@pytest.mark.anyio
async def test_mock_fails_general_questions():
    prompts = [
        "What is 17 times 23?",
        "What is the chemical symbol for gold?",
        "Who wrote Pride and Prejudice?",
    ]
    for prompt in prompts:
        response = await mock_provider.complete(ProviderRequest(prompt=prompt))
        assert response.text == "I don't know."
        assert response.provider == "mock"


@pytest.mark.anyio
async def test_mock_only_knows_sample_phrases():
    response = await mock_provider.complete(ProviderRequest(prompt="Capital of France?"))
    assert response.text == "Paris"


def test_models_endpoint_marks_mock_as_not_live():
    response = client.get("/api/models")
    assert response.status_code == 200
    models = {m["id"]: m for m in response.json()["models"]}
    if "mock-model-v1" in models:
        assert models["mock-model-v1"]["is_live"] is False
    for model_id in ("gemini-2.5-flash-lite", "gpt-4o-mini"):
        if model_id in models:
            assert models[model_id]["is_live"] is True