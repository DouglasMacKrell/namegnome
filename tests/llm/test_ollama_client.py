"""Tests for the Ollama async client wrapper (generate function).

Covers expected-flow, edge, and failure cases for streaming and error handling.
"""

import json
from typing import Any

import httpx
import pytest
import respx

from namegnome.llm.ollama_client import LLMUnavailableError, generate


@pytest.mark.asyncio
@respx.mock
async def test_generate_success_stream(monkeypatch: Any) -> None:
    """Test generate() returns concatenated output from a successful Ollama streaming response."""
    model = "test-model"
    prompt = "Say hello"
    response_chunks = [
        {"response": "Hello, "},
        {"response": "world!"},
        {"done": True},
    ]

    # Simulate streaming JSON lines
    async def mock_aiter_bytes() -> Any:
        for chunk in response_chunks:
            yield (httpx.ByteStream((json.dumps(chunk) + "\n").encode()))

    # Patch httpx.AsyncClient.post to return a mock response
    class MockResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.aiter_bytes_called = False

        async def aiter_bytes(self) -> Any:
            self.aiter_bytes_called = True
            for chunk in response_chunks:
                yield (json.dumps(chunk) + "\n").encode()

    class MockAsyncClient:
        async def __aenter__(self) -> Any:
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            pass

        async def post(self, *args: Any, **kwargs: Any) -> Any:
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    result = await generate(model, prompt, stream=True)
    assert result == "Hello, world!"


@pytest.mark.asyncio
@respx.mock
async def test_generate_only_done_chunk(monkeypatch: Any) -> None:
    """Test generate() returns empty string if only a 'done' chunk is received."""
    model = "test-model"
    prompt = "Say nothing"
    response_chunks = [{"done": True}]

    class MockResponse:
        def __init__(self) -> None:
            self.status_code = 200

        async def aiter_bytes(self) -> Any:
            for chunk in response_chunks:
                yield (json.dumps(chunk) + "\n").encode()

    class MockAsyncClient:
        async def __aenter__(self) -> Any:
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            pass

        async def post(self, *args: Any, **kwargs: Any) -> Any:
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    result = await generate(model, prompt, stream=True)
    assert result == ""


@pytest.mark.asyncio
@respx.mock
async def test_generate_connection_error(monkeypatch: Any) -> None:
    """Test generate() raises LLMUnavailableError on connection error."""
    model = "test-model"
    prompt = "fail"

    class MockAsyncClient:
        async def __aenter__(self) -> Any:
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            pass

        async def post(self, *args: Any, **kwargs: Any) -> Any:
            raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    with pytest.raises(LLMUnavailableError):
        await generate(model, prompt, stream=True)
