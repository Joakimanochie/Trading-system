"""
Singleton OpenAI client pointed at NVIDIA NIM (GLM-5.1).
This is the ONLY LLM dependency across all agents — no other AI SDK is imported anywhere.
"""
from __future__ import annotations

import os

from openai import OpenAI

_client: OpenAI | None = None


def get_nim_client() -> OpenAI:
    """Return a singleton OpenAI client pointed at NVIDIA NIM."""
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=os.environ["NVIDIA_NIM_BASE_URL"],
            api_key=os.environ["NVIDIA_API_KEY"],
        )
    return _client


def nim_complete(
    prompt: str,
    system: str = "",
    temperature: float = 0.6,
    max_tokens: int = 2048,
    stream: bool = False,
) -> str:
    """Single-turn completion via GLM-5.1. Returns full text response."""
    client = get_nim_client()
    model = os.environ.get("NVIDIA_NIM_MODEL", "z-ai/glm-5.1")

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
            top_p=float(os.environ.get("NVIDIA_NIM_TOP_P", "0.9")),
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
            top_p=float(os.environ.get("NVIDIA_NIM_TOP_P", "0.9")),
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content
