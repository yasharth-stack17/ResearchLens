"""Groq LLM provider with retries and local response caching."""
import hashlib
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/cache/llm"
DEFAULT_MODEL = "openai/gpt-oss-120b"


class LLMError(Exception):
    pass


class MissingKeyError(LLMError):
    pass


class RateLimitError(LLMError):
    pass


def _load_env():
    path = ROOT / ".env"
    if not path.exists():
        return

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(
            key.strip(), value.strip().strip('"').strip("'")
        )


def generate(prompt, system="", use_cache=True, max_tokens=1200):
    """Generate text using Groq. Raises LLMError on failure."""
    _load_env()

    key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL") or DEFAULT_MODEL

    if not key:
        raise MissingKeyError("GROQ_API_KEY is missing from .env")

    digest = hashlib.sha256(
        json.dumps([model, system, prompt, max_tokens]).encode()
    ).hexdigest()
    cache_file = CACHE / f"{digest}.json"

    if use_cache and cache_file.exists():
        return json.loads(cache_file.read_text())["text"]

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_completion_tokens": max_tokens,
        "reasoning_effort": "low",
        "reasoning_format": "hidden",
    }

    error = None

    for attempt in range(3):
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json=payload,
                timeout=60,
            )
        except requests.RequestException as exc:
            error = LLMError(f"Groq network error: {exc}")
        else:
            if response.status_code == 200:
                try:
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"]
                except (ValueError, KeyError, IndexError, TypeError):
                    raise LLMError("Invalid Groq response format")

                if not isinstance(answer, str) or not answer.strip():
                    raise LLMError("Groq returned an empty answer")

                answer = answer.strip()

                if use_cache:
                    CACHE.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(json.dumps({"text": answer}))

                return answer

            if response.status_code == 429:
                error = RateLimitError("Groq rate limit reached")
            elif response.status_code >= 500:
                error = LLMError(
                    f"Groq server error: HTTP {response.status_code}"
                )
            else:
                raise LLMError(
                    f"Groq HTTP {response.status_code}: "
                    f"{response.text[:200]}"
                )

        if attempt < 2:
            time.sleep(2 ** attempt)

    raise error or LLMError("Groq request failed")
