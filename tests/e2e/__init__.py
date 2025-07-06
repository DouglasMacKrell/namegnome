"""End-to-end testing module for NameGnome.

This module implements tiered end-to-end testing with graceful fallbacks
for both API access and LLM availability:

Test Tiers:
- Core E2E: cached API responses + deterministic LLM + file ops (no external deps)
- API E2E: real APIs + deterministic LLM + file ops (requires API keys)
- LLM E2E: cached APIs + real LLM + file ops (requires Ollama)
- Full E2E: real APIs + real LLM + file ops (requires both)

Usage:
    # Run all available E2E tests (auto-detects dependencies)
    NAMEGNOME_E2E_TESTS=1 pytest tests/e2e/

    # Run only Core E2E tests (no external dependencies)
    NAMEGNOME_E2E_TESTS=1 pytest tests/e2e/ -m "not api and not llm"

    # Run API tests only
    NAMEGNOME_E2E_TESTS=1 pytest tests/e2e/ -m "api and not llm"

    # Run LLM tests only
    NAMEGNOME_E2E_TESTS=1 pytest tests/e2e/ -m "llm and not api"

    # Run Full E2E tests
    NAMEGNOME_E2E_TESTS=1 pytest tests/e2e/ -m "api and llm"

Test markers:
- @pytest.mark.e2e: All end-to-end tests
- @pytest.mark.api: Tests requiring real API keys
- @pytest.mark.llm: Tests requiring real Ollama instance
"""
