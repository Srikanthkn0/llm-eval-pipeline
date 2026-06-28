import asyncio
import time

import httpx

from app.config import settings
from app.providers.base import LLMProvider, ProviderRequest, ProviderResponse
from app.providers.openai_compatible import HTTP_HEADERS, _format_llm_error

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-2.5-flash-lite"


class GeminiProvider(LLMProvider):
    def __init__(self, *, api_key: str):
        self._api_key = api_key

    @property
    def id(self) -> str:
        return "gemini"

    @property
    def label(self) -> str:
        return "Gemini"

    def is_configured(self) -> bool:
        return bool(self._api_key.strip())

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.require_configured()

        chosen_model = request.model or DEFAULT_MODEL
        url = f"{GEMINI_BASE_URL}/{chosen_model}:generateContent"
        params = {"key": self._api_key}
        payload = {
            "contents": [{"parts": [{"text": request.prompt}]}],
            "generationConfig": {"temperature": 0},
        }

        start = time.perf_counter()
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=settings.LLM_REQUEST_TIMEOUT_SEC) as client:
            for attempt in range(settings.LLM_MAX_RETRIES + 1):
                try:
                    response = await client.post(
                        url,
                        params=params,
                        headers=HTTP_HEADERS,
                        json=payload,
                    )
                    if response.status_code >= 400:
                        body = response.text
                        if (
                            response.status_code in {429, 500, 502, 503, 504}
                            and attempt < settings.LLM_MAX_RETRIES
                        ):
                            await asyncio.sleep(0.5 * (attempt + 1))
                            continue
                        raise _format_llm_error(response.status_code, body, self.label)
                    data = response.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    latency_ms = (time.perf_counter() - start) * 1000
                    return ProviderResponse(
                        text=text,
                        provider=self.id,
                        model=chosen_model,
                        latency_ms=latency_ms,
                    )
                except httpx.HTTPError as exc:
                    last_error = RuntimeError(f"{self.label} request failed: {exc}")
                    if attempt < settings.LLM_MAX_RETRIES:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    raise last_error from exc

        raise last_error or RuntimeError(f"{self.label} request failed")


def build_gemini_provider() -> GeminiProvider:
    return GeminiProvider(api_key=settings.GEMINI_API_KEY)