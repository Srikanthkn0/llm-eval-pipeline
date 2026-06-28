import asyncio
import time

import httpx

from app.config import settings
from app.providers.base import LLMProvider, ProviderRequest, ProviderResponse

HTTP_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "llm-eval-pipeline/1.0",
    "Accept": "application/json",
}


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


class OpenAICompatibleProvider(LLMProvider):
    # OpenAI-style /chat/completions. OpenAI and Groq share this.

    def __init__(
        self,
        *,
        provider_id: str,
        label: str,
        api_key: str,
        base_url: str,
        default_model: str,
    ):
        self._id = provider_id
        self._label = label
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model

    @property
    def id(self) -> str:
        return self._id

    @property
    def label(self) -> str:
        return self._label

    def is_configured(self) -> bool:
        return bool(self._api_key.strip())

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.require_configured()

        chosen_model = request.model or self._default_model
        payload = {
            "model": chosen_model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": 0,
        }
        headers = {**HTTP_HEADERS, "Authorization": f"Bearer {self._api_key}"}

        start = time.perf_counter()
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=settings.LLM_REQUEST_TIMEOUT_SEC) as client:
            for attempt in range(settings.LLM_MAX_RETRIES + 1):
                try:
                    response = await client.post(
                        f"{self._base_url}/chat/completions",
                        headers=headers,
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
                        raise _format_llm_error(response.status_code, body, self._label)
                    data = response.json()
                    text = data["choices"][0]["message"]["content"].strip()
                    latency_ms = (time.perf_counter() - start) * 1000
                    return ProviderResponse(
                        text=text,
                        provider=self.id,
                        model=chosen_model,
                        latency_ms=latency_ms,
                    )
                except httpx.HTTPError as exc:
                    last_error = RuntimeError(f"{self._label} request failed: {exc}")
                    if attempt < settings.LLM_MAX_RETRIES:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    raise last_error from exc

        raise last_error or RuntimeError(f"{self._label} request failed")


def missing_key_message(provider_id: str) -> str:
    env_name = {
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider_id, "API key")
    return f"{provider_id.title()} provider requires {env_name} on the server."