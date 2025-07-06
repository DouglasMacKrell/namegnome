# End-to-End Testing Guide

NameGnome implements a comprehensive tiered end-to-end testing system that validates the complete pipeline with varying levels of external dependencies. This system builds on the existing regression testing infrastructure but tests with real external services.

## Testing Tiers

### 🟢 Core E2E (No Dependencies)
- **What**: Cached API responses + deterministic LLM + real file operations
- **Dependencies**: None (fully self-contained)
- **When**: Every PR and push to main/develop
- **Purpose**: Validate core functionality without external dependencies
- **Tests**: 2 tests covering scan→undo cycle and visual CLI elements

### 🟡 API E2E (Requires API Keys)  
- **What**: Real API calls + deterministic LLM + real file operations
- **Dependencies**: Real API keys (TVDB, TMDB, OMDb)
- **When**: Nightly scheduled runs or manual execution
- **Purpose**: Validate API integration and metadata quality
- **Tests**: 2 tests covering real API integration and provider fallback

### 🟠 LLM E2E (Requires Ollama)
- **What**: Cached APIs + real LLM + real file operations  
- **Dependencies**: Real Ollama instance
- **When**: Local development and manual testing
- **Purpose**: Validate LLM integration and confidence thresholds
- **Tests**: 2 tests covering real LLM processing and confidence handling

### 🔴 Full E2E (Requires Both)
- **What**: Real APIs + real LLM + real file operations
- **Dependencies**: Real API keys + Real Ollama
- **When**: Local development and comprehensive validation
- **Purpose**: Complete end-to-end pipeline validation
- **Tests**: 2 tests covering complete pipeline and series disambiguation

## Usage Examples

### Running Tests Locally

```bash
# Enable E2E testing (required for all E2E tests)
export NAMEGNOME_E2E_TESTS=1

# Run Core E2E (no dependencies required)
pytest tests/e2e/ -m "not api and not llm" -v

# Run API E2E (requires API keys)
export TVDB_API_KEY="your_tvdb_key"  # pragma: allowlist secret
export TMDB_API_KEY="your_tmdb_key"  # pragma: allowlist secret
export OMDB_API_KEY="your_omdb_key"  # pragma: allowlist secret
pytest tests/e2e/ -m "api and not llm" -v

# Run LLM E2E (requires Ollama running)
pytest tests/e2e/ -m "llm and not api" -v

# Run Full E2E (requires both API keys and Ollama)
pytest tests/e2e/ -m "api and llm" -v

# Run all available E2E tests (auto-detects dependencies)
pytest tests/e2e/ -v
```

### Non-Interactive Mode

All E2E tests run in non-interactive mode by default:

```bash
# Tests automatically set these environment variables:
NAMEGNOME_NON_INTERACTIVE=1
NAMEGNOME_NO_RICH=1  # For JSON output tests
```

### Poetry Integration

Since NameGnome uses Poetry for dependency management, use Poetry to run tests:

```bash
# Run Core E2E tests with Poetry
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/ -m "not api and not llm" -v

# Run with API keys
NAMEGNOME_E2E_TESTS=1 TVDB_API_KEY="key" poetry run pytest tests/e2e/ -m "api and not llm" -v  # pragma: allowlist secret
```

## Test Architecture

### Dependency Detection

Tests automatically detect available dependencies:

- **API Keys**: Check environment variables `TVDB_API_KEY`, `TMDB_API_KEY`, `OMDB_API_KEY`
- **Ollama**: Attempt connection to `http://localhost:11434` 
- **Graceful Fallback**: Tests skip with clear messages if dependencies unavailable

### Cached Fixtures

Core E2E tests use cached API responses stored in `tests/e2e/fixtures/`:

```
tests/e2e/fixtures/
├── tvdb/
│   ├── search_danger_mouse.json
│   └── episodes_danger_mouse.json
├── tmdb/
│   ├── search_danger_mouse.json
│   └── season_danger_mouse.json
└── omdb/
    └── search_danger_mouse.json
```

These fixtures are generated from real API calls and provide deterministic responses for dependency-free testing.

### Test Isolation

Each test uses isolated temporary directories:

- Tests create unique `tmpdir` for each execution
- Original files are verified unchanged after undo operations
- No cross-test contamination or state sharing

## CI Integration

### GitHub Actions Workflow

The `.github/workflows/e2e.yml` workflow provides:

**Core E2E on Every PR:**
- Runs on `push` and `pull_request` events
- No external dependencies required
- Fast execution (~40 seconds total)
- Blocks merging if tests fail

**Extended E2E Nightly:**
- Runs on scheduled cron at 3 AM UTC
- Tests API integration when secrets available
- Cross-platform testing (Ubuntu, macOS)
- Optional manual triggering via `workflow_dispatch`

### Environment Variables

CI automatically sets required environment variables:

```yaml
env:
  CI: "true"
  PYTHONPATH: ${{ github.workspace }}
  NAMEGNOME_NON_INTERACTIVE: "true"
  # API keys from GitHub secrets (for nightly runs)
  TVDB_API_KEY: ${{ secrets.TVDB_API_KEY }}
  TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}
  OMDB_API_KEY: ${{ secrets.OMDB_API_KEY }}
```

## Test Specifications

### Core E2E Tests

**test_core_e2e_scan_apply_undo_cycle:**
- Creates test files with realistic TV show names
- Runs complete scan with cached APIs and deterministic LLM
- Validates JSON output structure and field names
- Tests undo functionality with plan ID
- Verifies original files unchanged
- Performance validation (<30 seconds)

**test_core_e2e_visual_elements:**
- Tests Rich console output and visual elements
- Validates NameGnome banner display
- Checks for gnome emoji indicators
- Verifies Rich table formatting
- Ensures visual CLI works in non-interactive mode

### API E2E Tests

**test_api_e2e_real_tvdb_integration:**
- Uses real TVDB API with actual API keys
- Tests metadata quality with real episode data
- Validates destination path structure
- Checks provider response handling

**test_api_e2e_provider_fallback_real:**
- Tests provider fallback mechanisms
- Validates graceful handling of API failures
- Ensures robust error handling

### LLM E2E Tests

**test_llm_e2e_real_ollama_integration:**
- Uses real Ollama LLM instance
- Tests LLM processing with cached APIs
- Validates confidence score handling
- Checks LLM response integration

**test_llm_e2e_confidence_thresholds:**
- Tests challenging filename scenarios
- Validates confidence threshold behavior
- Ensures proper manual flagging

### Full E2E Tests

**test_full_e2e_complete_pipeline:**
- Tests complete pipeline with all external dependencies
- Validates highest quality results
- Performance testing for full stack
- End-to-end integration validation

**test_full_e2e_series_disambiguation:**
- Tests series disambiguation with real data
- Validates multi-series handling
- Checks auto-selection behavior

## Performance Characteristics

### Execution Times

Based on local testing:

- **Core E2E**: ~40 seconds (includes actual file scanning)
- **API E2E**: ~1.3 seconds (cached LLM makes it fast)
- **LLM E2E**: ~1.2 seconds (cached APIs make it fast)
- **Full E2E**: ~1.2 seconds (optimized with caching)

### Performance Validation

All E2E tests include performance guards:

```python
# Each test includes timing validation
start_time = time.time()
# ... test execution ...
elapsed = time.time() - start_time
assert elapsed < 30, f"E2E test took too long: {elapsed:.2f}s"
```

## Debugging and Troubleshooting

### Common Issues

**Tests skip with "No JSON output":**
- Check that scan actually produces JSON output
- Verify file naming follows expected patterns
- Ensure `--json` flag is working correctly

**API tests fail with authentication errors:**
- Verify API keys are correctly set
- Check API key validity and rate limits
- Ensure network connectivity to external APIs

**LLM tests skip or fail:**
- Verify Ollama is running on `localhost:11434`
- Check that required models are installed
- Ensure sufficient system resources for LLM

### Debug Commands

```bash
# Test individual tiers
NAMEGNOME_E2E_TESTS=1 pytest tests/e2e/test_real_tv_scan.py::TestTVScanEndToEnd::test_core_e2e_scan_apply_undo_cycle -v

# Run with detailed output
NAMEGNOME_E2E_TESTS=1 pytest tests/e2e/ -v -s --tb=long

# Check environment detection
NAMEGNOME_E2E_TESTS=1 pytest tests/e2e/ -v --collect-only
```

### Manual Testing

For manual validation outside pytest:

```bash
# Test Core E2E manually
cd /tmp && mkdir test_e2e && cd test_e2e
mkdir "Danger Mouse 2015"
echo "fake content" > "Danger Mouse 2015/Danger Mouse 2015-S01E01-Test.mp4"

# Run scan with Core E2E settings
NAMEGNOME_E2E_TESTS=1 NAMEGNOME_NON_INTERACTIVE=1 poetry run python -m namegnome scan --media-type tv --json .
```

## Contributing

When adding new E2E tests:

1. **Follow tier structure**: Mark tests with appropriate `@pytest.mark.api` and `@pytest.mark.llm`
2. **Use proper fixtures**: Create cached API responses for Core E2E
3. **Ensure isolation**: Use `tmpdir` for all file operations
4. **Add performance guards**: Include timing validation
5. **Document dependencies**: Clear error messages when dependencies missing
6. **Test graceful fallbacks**: Verify behavior when external services unavailable

The E2E testing system is designed to provide comprehensive validation while remaining practical for CI and local development workflows. 