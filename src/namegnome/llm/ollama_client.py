"""Ollama client async wrapper module.

Provides an asynchronous interface to a local Ollama server for LLM inference.
Exposes the generate() function for streaming or non-streaming text generation.
Raises LLMUnavailableError on connection issues.
"""

import json

import httpx

from namegnome.metadata.cache import (
    cache,  # Reuse generic SQLite cache for LLM responses (Sprint 3.7)
)


class LLMUnavailableError(Exception):
    """Raised when the Ollama server is unavailable or times out."""

    pass


class PromptTooLargeError(Exception):
    """Raised when the LLM prompt exceeds allowed size limits (10,000 chars or 2MB)."""

    pass


PROMPT_CHAR_LIMIT = 10000  # Maximum allowed prompt length in characters
PROMPT_BYTE_LIMIT = 2 * 1024 * 1024  # Maximum allowed prompt size in bytes (2MB)


@cache(ttl=86400)
async def generate(model: str, prompt: str, stream: bool = True) -> str:
    """Generate text from a local Ollama server asynchronously.

    Args:
        model (str): The model name to use (e.g., 'llama2', 'deepseek-coder').
        prompt (str): The prompt to send to the model.
        stream (bool): Whether to stream the response (default: True).

    Returns:
        str: The concatenated response text from the Ollama server.

    Raises:
        LLMUnavailableError: If the Ollama server is unreachable or times out.
        PromptTooLargeError: If the prompt exceeds PROMPT_CHAR_LIMIT or
            PROMPT_BYTE_LIMIT.

    This function posts to the Ollama /api/generate endpoint and yields the
    concatenated 'response' fields from the streamed JSON lines. If the server
    is unavailable, it raises LLMUnavailableError.
    """
    # Prompt size guard: PROMPT_CHAR_LIMIT chars or PROMPT_BYTE_LIMIT bytes
    if (
        len(prompt) > PROMPT_CHAR_LIMIT
        or len(prompt.encode("utf-8")) > PROMPT_BYTE_LIMIT
    ):
        raise PromptTooLargeError(
            f"Prompt exceeds {PROMPT_CHAR_LIMIT} characters or "
            f"{PROMPT_BYTE_LIMIT // (1024 * 1024)}MB."
        )
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": stream}
    output = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=30)
            async for chunk in resp.aiter_bytes():
                for line in chunk.splitlines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    if "response" in data:
                        output.append(data["response"])
    except httpx.ConnectError as exc:
        raise LLMUnavailableError("Ollama server unavailable") from exc
    return "".join(output)
