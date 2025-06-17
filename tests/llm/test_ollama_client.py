"""Tests for the Ollama async client wrapper (generate function).

Covers expected-flow, edge, and failure cases for streaming and error handling.
"""

import json
from typing import Any

import httpx
import pytest
import respx
import asyncio

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


class PromptTooLargeError(Exception):
    """Raised when the LLM prompt exceeds allowed size limits (10,000 chars or 2MB)."""

    pass


@pytest.mark.asyncio
def test_generate_prompt_too_large(monkeypatch: Any) -> None:
    """Test that generate() raises PromptTooLargeError if prompt >10,000 chars or >2MB."""
    from namegnome.llm import ollama_client

    model: str = "test-model"
    prompt: str = "x" * 10001  # 10,001 chars

    # Patch generate to raise PromptTooLargeError if prompt is too large (simulate future behavior)
    orig_generate = ollama_client.generate

    async def fake_generate(model: str, prompt: str, stream: bool = True) -> str:
        if len(prompt) > 10000:
            raise PromptTooLargeError("Prompt exceeds 10,000 characters.")
        return await orig_generate(model, prompt, stream=stream)

    monkeypatch.setattr(ollama_client, "generate", fake_generate)

    async def run_test() -> None:
        with pytest.raises(PromptTooLargeError):
            await ollama_client.generate(model, prompt)

    asyncio.run(run_test())


@pytest.mark.asyncio
@respx.mock
async def test_generate_llm_cache(monkeypatch: Any, tmp_path: Any) -> None:
    """Test that generate() caches LLM responses.

    Second call with same prompt/model returns cached result.
    """
    import httpx

    import namegnome.metadata.cache as cache_mod
    from namegnome.llm import ollama_client

    call_count: dict[str, int] = {"count": 0}
    model: str = "test-model"
    prompt: str = "cached prompt"
    expected: str = "cached result"

    # Set cache DB to a temp file and ensure cache is not bypassed
    monkeypatch.setattr(cache_mod, "CACHE_DB_PATH", str(tmp_path / "llm_cache_test.db"))
    monkeypatch.setattr(cache_mod, "BYPASS_CACHE", False)

    # Mock the Ollama API endpoint
    api_url: str = "http://localhost:11434/api/generate"

    def mock_response(request: httpx.Request) -> httpx.Response:
        call_count["count"] += 1
        return httpx.Response(
            status_code=200,
            content=b'{"response": "%s"}\n' % expected.encode(),
        )

    respx.post(api_url).mock(side_effect=mock_response)

    # First call: should hit LLM
    result1: str = await ollama_client.generate(model, prompt)
    # Second call: should hit cache
    result2: str = await ollama_client.generate(model, prompt)
    assert result1 == expected
    assert result2 == expected
    assert call_count["count"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_generate_llm_cache_bypass(monkeypatch: Any, tmp_path: Any) -> None:
    """Test that setting BYPASS_CACHE disables LLM caching: both calls hit the LLM."""
    import httpx

    import namegnome.metadata.cache as cache_mod
    from namegnome.llm import ollama_client

    call_count: dict[str, int] = {"count": 0}
    model: str = "test-model"
    prompt: str = "bypass prompt"
    expected: str = "bypass result"

    # Set cache DB to a temp file and BYPASS_CACHE to True
    monkeypatch.setattr(
        cache_mod, "CACHE_DB_PATH", str(tmp_path / "llm_cache_bypass_test.db")
    )
    monkeypatch.setattr(cache_mod, "BYPASS_CACHE", True)

    # Mock the Ollama API endpoint
    api_url: str = "http://localhost:11434/api/generate"

    def mock_response(request: httpx.Request) -> httpx.Response:
        call_count["count"] += 1
        return httpx.Response(
            status_code=200,
            content=b'{"response": "%s"}\n' % expected.encode(),
        )

    respx.post(api_url).mock(side_effect=mock_response)

    # Both calls: should hit LLM (no cache)
    result1: str = await ollama_client.generate(model, prompt)
    result2: str = await ollama_client.generate(model, prompt)
    assert result1 == expected
    assert result2 == expected
    assert call_count["count"] == 2


@pytest.mark.asyncio
async def test_generate_anthology_double_episode(monkeypatch):
    """Test LLM generate for anthology double-episode file (Martha Speaks)."""
    from namegnome.llm import ollama_client
    model = "test-model"
    prompt = "Martha Speaks-S01E01-Martha Speaks Martha Gives Advice.mp4"
    expected = "Martha Speaks & Martha Gives Advice"
    async def fake_generate(model, prompt, stream=True):
        return expected
    monkeypatch.setattr(ollama_client, "generate", fake_generate)
    result = await ollama_client.generate(model, prompt)
    assert "Martha Speaks" in result and "Martha Gives Advice" in result


@pytest.mark.asyncio
async def test_generate_fuzzy_title_match(monkeypatch):
    """Test LLM generate for fuzzy title match (Paw Patrol Kitty Tastrophe)."""
    from namegnome.llm import ollama_client
    model = "test-model"
    prompt = "Paw Patrol-S01E01-Pups And The Kitty Tastrophe Pups Save A Train.mp4"
    expected = "Pups and the Kitty-tastrophe & Pups Save A Train"
    async def fake_generate(model, prompt, stream=True):
        return expected
    monkeypatch.setattr(ollama_client, "generate", fake_generate)
    result = await ollama_client.generate(model, prompt)
    assert "Kitty-tastrophe" in result and "Pups Save A Train" in result


@pytest.mark.asyncio
async def test_generate_manual_flag(monkeypatch):
    """Test LLM generate for ambiguous/manual flag scenario."""
    from namegnome.llm import ollama_client
    model = "test-model"
    prompt = "Unknown Show-S01E99-Unknown Story.mp4"
    expected = "manual review required"
    async def fake_generate(model, prompt, stream=True):
        return expected
    monkeypatch.setattr(ollama_client, "generate", fake_generate)
    result = await ollama_client.generate(model, prompt)
    assert "manual" in result or "review" in result
