"""Smoke tests for NVIDIA NIM client (mocked)."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch


def test_nim_complete_non_streaming():
    """nim_complete should call the OpenAI client and return a string."""
    os.environ.setdefault("NVIDIA_API_KEY", "test-key")
    os.environ.setdefault("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    os.environ.setdefault("NVIDIA_NIM_MODEL", "z-ai/glm-5.1")

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hello from GLM-5.1"

    with patch("agents.shared.nim_client._client", None):
        with patch("agents.shared.nim_client.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            MockOpenAI.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response

            from agents.shared.nim_client import nim_complete

            result = nim_complete("Say hello.", stream=False)
            assert isinstance(result, str)
            assert len(result) > 0


def test_nim_complete_returns_string_on_stream():
    """nim_complete with stream=True should assemble chunks and return a string."""
    os.environ.setdefault("NVIDIA_API_KEY", "test-key")

    chunk1 = MagicMock()
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta.content = "Hello "

    chunk2 = MagicMock()
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta.content = "world"

    with patch("agents.shared.nim_client._client", None):
        with patch("agents.shared.nim_client.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            MockOpenAI.return_value = mock_client
            mock_client.chat.completions.create.return_value = iter([chunk1, chunk2])

            from agents.shared.nim_client import nim_complete

            result = nim_complete("test", stream=True)
            assert "Hello" in result
