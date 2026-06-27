"""
LLM completion client.

- mock-model-v1: deterministic demo model for local dev and CI (no API key).
  Pattern-matches common trivia questions; returns "I don't know." otherwise.
- Any other model name: calls OpenAI Chat Completions when OPENAI_API_KEY is set.
"""
import asyncio
import json
import time
import urllib.error
import urllib.request

from app.config import settings


def build_prompt(template: str, user_input: str) -> str:
    return template.replace("{input}", user_input)


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


async def _openai_generate(prompt: str, model: str) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        },
        method="POST",
    )

    def _call_api() -> str:
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API error ({exc.code}): {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc.reason}") from exc

    return await asyncio.to_thread(_call_api)


async def generate_completion(prompt: str, model_name: str) -> tuple[str, float]:
    start = time.perf_counter()

    use_openai = bool(settings.OPENAI_API_KEY) and not model_name.startswith("mock-")
    if use_openai:
        text = await _openai_generate(prompt, model_name)
    else:
        text = await _mock_generate(prompt)

    latency_ms = (time.perf_counter() - start) * 1000
    return text, latency_ms