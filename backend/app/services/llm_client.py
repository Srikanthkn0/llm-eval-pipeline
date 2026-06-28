# Thin facade over app.providers. Groq often fails on cloud IPs (CF 1010) — use Gemini on Render.
from app.providers.registry import (
    complete,
    list_available_models,
    provider_status,
    validate_model_choice,
)

__all__ = [
    "build_prompt",
    "complete",
    "generate_completion",
    "list_available_models",
    "provider_status",
    "validate_model_choice",
]


def build_prompt(template: str, user_input: str) -> str:
    return template.replace("{input}", user_input)


async def generate_completion(prompt: str, model_name: str) -> tuple[str, float]:
    response = await complete(prompt, model_name)
    return response.text, response.latency_ms