from app.config import settings
from app.providers.openai_compatible import OpenAICompatibleProvider

OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"


def build_openai_provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        provider_id="openai",
        label="OpenAI",
        api_key=settings.OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        default_model=DEFAULT_MODEL,
    )