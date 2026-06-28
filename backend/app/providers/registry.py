from typing import TypedDict

from fastapi import HTTPException

from app.config import settings
from app.providers.base import LLMProvider, ProviderRequest, ProviderResponse
from app.providers.gemini_provider import build_gemini_provider
from app.providers.groq_provider import build_groq_provider
from app.providers.mock_provider import mock_provider
from app.providers.openai_compatible import missing_key_message
from app.providers.openai_provider import build_openai_provider


class ModelMeta(TypedDict):
    provider: str
    label: str
    requires_key: str | bool


MODEL_REGISTRY: dict[str, ModelMeta] = {
    "mock-model-v1": {
        "provider": "mock",
        "label": "Mock — hardcoded answers, no API call",
        "requires_key": False,
    },
    "gemini-2.5-flash-lite": {
        "provider": "gemini",
        "label": "Gemini 2.5 Flash-Lite",
        "requires_key": "GEMINI_API_KEY",
    },
    "gemini-2.5-flash": {
        "provider": "gemini",
        "label": "Gemini 2.5 Flash",
        "requires_key": "GEMINI_API_KEY",
    },
    "llama-3.1-8b-instant": {
        "provider": "groq",
        "label": "Llama 3.1 8B (Groq, may fail on cloud hosts)",
        "requires_key": "GROQ_API_KEY",
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "label": "GPT-4o mini (OpenAI)",
        "requires_key": "OPENAI_API_KEY",
    },
}


def get_registry() -> dict[str, LLMProvider]:
    # Rebuilt each call so tests can patch env vars.
    return {
        mock_provider.id: mock_provider,
        "openai": build_openai_provider(),
        "groq": build_groq_provider(),
        "gemini": build_gemini_provider(),
    }


def get_provider(provider_id: str) -> LLMProvider | None:
    return get_registry().get(provider_id)


def _remote_model(model_name: str) -> str:
    return model_name


def list_available_models() -> list[dict[str, str | bool]]:
    models: list[dict[str, str | bool]] = []
    for model_id, meta in MODEL_REGISTRY.items():
        if meta["provider"] == "mock":
            if settings.mock_allowed:
                models.append(
                    {
                        "id": model_id,
                        "label": str(meta["label"]),
                        "provider": "mock",
                        "available": True,
                        "is_live": False,
                    }
                )
            continue

        key_name = str(meta["requires_key"])
        if getattr(settings, key_name, ""):
            models.append(
                {
                    "id": model_id,
                    "label": str(meta["label"]),
                    "provider": str(meta["provider"]),
                    "available": True,
                    "is_live": True,
                }
            )
    return models


def validate_model_choice(model_name: str) -> None:
    if model_name not in MODEL_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{model_name}'. Use GET /api/models for available models.",
        )

    meta = MODEL_REGISTRY[model_name]
    if meta["provider"] == "mock":
        if not settings.mock_allowed:
            raise HTTPException(
                status_code=400,
                detail=(
                    "mock-model-v1 is disabled in production. "
                    "Configure GEMINI_API_KEY, OPENAI_API_KEY, or GROQ_API_KEY."
                ),
            )
        return

    key_name = str(meta["requires_key"])
    if not getattr(settings, key_name, ""):
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model_name}' requires {key_name} on the server.",
        )


async def complete(prompt: str, model_name: str) -> ProviderResponse:
    validate_model_choice(model_name)
    meta = MODEL_REGISTRY[model_name]
    provider = get_provider(meta["provider"])
    if provider is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider '{meta['provider']}' for model '{model_name}'.",
        )

    if not provider.is_configured():
        raise HTTPException(
            status_code=400,
            detail=missing_key_message(meta["provider"]),
        )

    return await provider.complete(
        ProviderRequest(prompt=prompt, model=_remote_model(model_name))
    )


def provider_status() -> dict[str, bool]:
    registry = get_registry()
    return {
        "gemini": registry["gemini"].is_configured(),
        "groq": registry["groq"].is_configured(),
        "openai": registry["openai"].is_configured(),
        "mock_allowed": settings.mock_allowed,
    }