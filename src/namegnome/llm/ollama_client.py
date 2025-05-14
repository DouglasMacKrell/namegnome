"""Ollama client async wrapper module.

Provides an asynchronous interface to a local Ollama server for LLM inference.
Exposes the generate() function for streaming or non-streaming text generation.
Raises LLMUnavailableError on connection issues.
"""

import json

import httpx


class LLMUnavailableError(Exception):
    """Raised when the Ollama server is unavailable or times out."""

    pass


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

    This function posts to the Ollama /api/generate endpoint and yields the
    concatenated 'response' fields from the streamed JSON lines. If the server
    is unavailable, it raises LLMUnavailableError.
    """
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
