from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderRequest:
    prompt: str
    model: str | None = None


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    provider: str
    model: str
    latency_ms: float


class ProviderNotConfiguredError(Exception):
    def __init__(self, provider_id: str, detail: str):
        self.provider_id = provider_id
        self.detail = detail
        super().__init__(detail)


class LLMProvider(ABC):

    @property
    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def label(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError

    def require_configured(self) -> None:
        if not self.is_configured():
            raise ProviderNotConfiguredError(
                self.id,
                f"Provider '{self.id}' is not configured on this server.",
            )