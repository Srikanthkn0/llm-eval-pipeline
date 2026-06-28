from app.config import settings
from app.providers.openai_compatible import OpenAICompatibleProvider

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.1-8b-instant"


def build_groq_provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        provider_id="groq",
        label="Groq",
        api_key=settings.GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        default_model=DEFAULT_MODEL,
    )