"""
Singleton OpenAI client pointed at OpenRouter (owl-alpha).
This is the ONLY LLM dependency across all agents — no other AI SDK is imported anywhere.
"""
from __future__ import annotations

import os

from openai import OpenAI

_client: OpenAI | None = None


def get_llm_client() -> OpenAI:
    """Return a singleton OpenAI client pointed at OpenRouter."""
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.environ["OPENROUTER_API_KEY"],
            timeout=120.0,
        )
    return _client


# Keep backward-compatible alias
get_nim_client = get_llm_client


def nim_complete(
    prompt: str,
    system: str = "",
    temperature: float = 0.6,
    max_tokens: int = 2048,
    stream: bool = False,
) -> str:
    """Single-turn completion via OpenRouter. Returns full text response."""
    client = get_llm_client()
    model = os.environ.get("OPENROUTER_MODEL", "openrouter/owl-alpha")

    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    if stream:
        response_text = ""
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in completion:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and getattr(delta, "content", None):
                response_text += delta.content
        return response_text
    else:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content
