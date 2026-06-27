"""
LLM completion client with provider routing, retries, and production safeguards.
"""
import asyncio
import json
import time
import urllib.error
import urllib.request

from fastapi import HTTPException

from app.config import settings

GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENAI_BASE_URL = "https://api.openai.com/v1/chat/completions"

MODEL_REGISTRY = {
    "mock-model-v1": {
        "provider": "mock",
        "label": "Mock (CI/local only)",
        "requires_key": False,
    },
    "llama-3.1-8b-instant": {
        "provider": "groq",
        "label": "Llama 3.1 8B (Groq)",
        "requires_key": "GROQ_API_KEY",
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "label": "GPT-4o mini (OpenAI)",
        "requires_key": "OPENAI_API_KEY",
    },
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
        available = bool(getattr(settings, key_name, ""))
        if available:
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
                detail="mock-model-v1 is disabled in production. Configure GROQ_API_KEY or OPENAI_API_KEY.",
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


def _chat_completion(url: str, api_key: str, model: str, prompt: str) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    last_error: Exception | None = None
    for attempt in range(settings.LLM_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=settings.LLM_REQUEST_TIMEOUT_SEC) as response:
                body = json.loads(response.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(f"LLM API error ({exc.code}): {error_body}")
            if exc.code in {429, 500, 502, 503, 504} and attempt < settings.LLM_MAX_RETRIES:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise last_error from exc
        except urllib.error.URLError as exc:
            last_error = RuntimeError(f"LLM request failed: {exc.reason}")
            if attempt < settings.LLM_MAX_RETRIES:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise last_error from exc

    raise last_error or RuntimeError("LLM request failed")


async def generate_completion(prompt: str, model_name: str) -> tuple[str, float]:
    validate_model_choice(model_name)
    meta = MODEL_REGISTRY[model_name]
    start = time.perf_counter()

    if meta["provider"] == "mock":
        text = await _mock_generate(prompt)
    elif meta["provider"] == "groq":
        text = await asyncio.to_thread(
            _chat_completion,
            GROQ_BASE_URL,
            settings.GROQ_API_KEY,
            model_name,
            prompt,
        )
    else:
        text = await asyncio.to_thread(
            _chat_completion,
            OPENAI_BASE_URL,
            settings.OPENAI_API_KEY,
            model_name,
            prompt,
        )

    latency_ms = (time.perf_counter() - start) * 1000
    return text, latency_ms


def provider_status() -> dict[str, bool]:
    return {
        "groq": bool(settings.GROQ_API_KEY),
        "openai": bool(settings.OPENAI_API_KEY),
        "mock_allowed": settings.ALLOW_MOCK_MODEL or not settings.is_production,
    }