import asyncio
import time

from app.providers.base import LLMProvider, ProviderRequest, ProviderResponse

DEFAULT_MODEL = "mock-model-v1"


class MockProvider(LLMProvider):
    # Fixed answers for local dev, CI, and prod fallback. No API key.

    @property
    def id(self) -> str:
        return "mock"

    @property
    def label(self) -> str:
        return "Mock (CI/local only)"

    def is_configured(self) -> bool:
        return True

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        start = time.perf_counter()
        await asyncio.sleep(0.05)

        model = request.model or DEFAULT_MODEL
        text = self._build_response(request.prompt)

        return ProviderResponse(
            text=text,
            provider=self.id,
            model=model,
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    def _build_response(self, prompt: str) -> str:
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


mock_provider = MockProvider()