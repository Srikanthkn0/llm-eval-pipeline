"""
LLM completion client with provider routing, retries, and production safeguards.

Note: Groq blocks many cloud/datacenter IPs (Cloudflare 1010). Use Gemini or OpenAI
on Render; Groq works better from residential/local networks.
"""
import asyncio
import time

import httpx
from fastapi import HTTPException

from app.config import settings

OPENAI_BASE_URL = "https://api.openai.com/v1/chat/completions"
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

MODEL_REGISTRY = {
    "mock-model-v1": {
        "provider": "mock",
        "label": "Mock (CI/local only)",
        "requires_key": False,
    },
    "gemini-2.5-flash-lite": {
        "provider": "gemini",
        "label": "Gemini 2.5 Flash-Lite",
        "requires_key": "GEMINI_API_KEY",
        "remote_model": "gemini-2.5-flash-lite",
    },
    "gemini-2.5-flash": {
        "provider": "gemini",
        "label": "Gemini 2.5 Flash",
        "requires_key": "GEMINI_API_KEY",
        "remote_model": "gemini-2.5-flash",
    },
    "llama-3.1-8b-instant": {
        "provider": "groq",
        "label": "Llama 3.1 8B (Groq — may fail on cloud hosts)",
        "requires_key": "GROQ_API_KEY",
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "label": "GPT-4o mini (OpenAI)",
        "requires_key": "OPENAI_API_KEY",
    },
}

HTTP_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "llm-eval-pipeline/1.0",
    "Accept": "application/json",
}


def build_prompt(template: str, user_input: str) -> str:
    return template.replace("{input}", user_input)


def list_available_models() -> list[dict[str, str | bool]]:
    models: list[dict[str, str | bool]] = []
    for model_id, meta in MODEL_REGISTRY.items():
        if meta["provider"] == "mock":
            if settings.ALLOW_MOCK_MODEL or not settings.is_production:
                models.append(
                    {
                        "id": model_id,
                        "label": str(meta["label"]),
                        "provider": "mock",
                        "available": True,
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
        if settings.is_production and not settings.ALLOW_MOCK_MODEL:
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


async def _mock_generate(prompt: str) -> str:
    await asyncio.sleep(0.05)
    lower = prompt.lower()
    if "2 + 2" in lower or "2+2" in lower:
        return "4"
    if "capital of france" in lower:
        return "Paris"
    if "color is the sky" in lower or "colour is the sky" in lower:
        return "blue"
    if "days are in a week" in lower:
        return "7"
    if "http stand for" in lower:
        return "Hypertext Transfer Protocol"
    return "I don't know."


def _format_llm_error(status_code: int, body: str, provider: str) -> RuntimeError:
    if status_code == 403 and "1010" in body:
        return RuntimeError(
            f"{provider} blocked this server's IP (Cloudflare 1010). "
            "Use Gemini with GEMINI_API_KEY on Render instead."
        )
    if status_code == 429:
        return RuntimeError(
            f"{provider} rate limit hit (429). Wait a minute and retry, "
            "or try gemini-2.5-flash-lite instead of gemini-2.5-flash."
        )
    return RuntimeError(f"{provider} API error ({status_code}): {body[:500]}")


async def _openai_compatible_completion(
    url: str,
    api_key: str,
    model: str,
    prompt: str,
    provider: str,
) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    headers = {**HTTP_HEADERS, "Authorization": f"Bearer {api_key}"}

    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=settings.LLM_REQUEST_TIMEOUT_SEC) as client:
        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code >= 400:
                    body = response.text
                    if response.status_code in {429, 500, 502, 503, 504} and attempt < settings.LLM_MAX_RETRIES:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    raise _format_llm_error(response.status_code, body, provider)
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except httpx.HTTPError as exc:
                last_error = RuntimeError(f"{provider} request failed: {exc}")
                if attempt < settings.LLM_MAX_RETRIES:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise last_error from exc

    raise last_error or RuntimeError(f"{provider} request failed")


async def _gemini_completion(model: str, prompt: str) -> str:
    remote_model = MODEL_REGISTRY[model].get("remote_model", model)
    url = f"{GEMINI_BASE_URL}/{remote_model}:generateContent"
    params = {"key": settings.GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0},
    }

    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=settings.LLM_REQUEST_TIMEOUT_SEC) as client:
        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                response = await client.post(url, params=params, headers=HTTP_HEADERS, json=payload)
                if response.status_code >= 400:
                    body = response.text
                    if response.status_code in {429, 500, 502, 503, 504} and attempt < settings.LLM_MAX_RETRIES:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    raise _format_llm_error(response.status_code, body, "Gemini")
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except httpx.HTTPError as exc:
                last_error = RuntimeError(f"Gemini request failed: {exc}")
                if attempt < settings.LLM_MAX_RETRIES:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise last_error from exc

    raise last_error or RuntimeError("Gemini request failed")


async def generate_completion(prompt: str, model_name: str) -> tuple[str, float]:
    validate_model_choice(model_name)
    meta = MODEL_REGISTRY[model_name]
    start = time.perf_counter()

    if meta["provider"] == "mock":
        text = await _mock_generate(prompt)
    elif meta["provider"] == "gemini":
        text = await _gemini_completion(model_name, prompt)
    elif meta["provider"] == "groq":
        text = await _openai_compatible_completion(
            GROQ_BASE_URL,
            settings.GROQ_API_KEY,
            model_name,
            prompt,
            "Groq",
        )
    else:
        text = await _openai_compatible_completion(
            OPENAI_BASE_URL,
            settings.OPENAI_API_KEY,
            model_name,
            prompt,
            "OpenAI",
        )

    latency_ms = (time.perf_counter() - start) * 1000
    return text, latency_ms


def provider_status() -> dict[str, bool]:
    return {
        "gemini": bool(settings.GEMINI_API_KEY),
        "groq": bool(settings.GROQ_API_KEY),
        "openai": bool(settings.OPENAI_API_KEY),
        "mock_allowed": settings.ALLOW_MOCK_MODEL or not settings.is_production,
    }