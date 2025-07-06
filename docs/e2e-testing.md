# End-to-End Testing Guide

This document describes NameGnome's comprehensive end-to-end (E2E) testing infrastructure, including our tiered dependency approach and complete anthology show coverage.

## Overview

NameGnome includes both **regression tests** (fast, mocked) and **end-to-end tests** (comprehensive, real dependencies) to ensure reliability:

- **Regression Tests**: Use mocked/stubbed providers for deterministic CI results, fast execution (<5 seconds), no network dependencies
- **End-to-End Tests**: Use real TVDB/TMDB/OMDb APIs, real LLM responses, real file operations, complete pipeline validation

## Test Architecture

### Core E2E Tests (TestTVScanEndToEnd)

Our E2E tests use a **tiered dependency approach** with automatic detection and graceful fallbacks:

1. **Core E2E** (no external deps): cached API responses + deterministic LLM + file ops
2. **API E2E** (requires API keys): real APIs + deterministic LLM + file ops  
3. **LLM E2E** (requires Ollama): cached APIs + real LLM + file ops
4. **Full E2E** (requires both): real APIs + real LLM + file ops

### Anthology Show Coverage (TestAnthologyShowsEndToEnd)

Our E2E testing includes comprehensive **anthology show coverage** that validates edge cases across all 6 shows in our fixture manifest:

**Shows Covered:**
- **Danger Mouse 2015** (non-anthology control) - Episodes per file: 1, standard TV naming
- **Firebuds** (anthology, trusted titles) - Episodes per file: 2, reliable episode titles  
- **Harvey Girls Forever!** (anthology, untrusted titles) - Episodes per file: 2, SONARR-style unreliable names
- **Martha Speaks** (anthology, edge cases) - Episodes per file: 2, apostrophes and same-name episodes
- **Paw Patrol** (anthology, complex mapping) - Complex episode mapping where file numbering doesn't match canonical TVDB order
- **The Octonauts** (anthology, title disambiguation) - Episodes per file: 1, "The Octonauts" vs "Octonauts" title handling

**Testing Strategy: Dual Approach**

We use a **dual testing strategy** to balance speed and comprehensiveness:

#### 1. **Sampling Tests** (Fast Feedback)
- Test 2-3 representative files per show (~14 total files)
- Focus on show-specific edge cases and characteristics  
- Complete in <30s for rapid development feedback
- Validate CLI flags: `--anthology`, `--untrusted-titles`, `--max-duration`

#### 2. **Volume Tests** (Comprehensive Coverage) 
- Process complete show directories (especially Paw Patrol with 291 files)
- **Critical for detecting mapping conflicts** that only emerge with full directory processing
- Example: Paw Patrol Season 1 shows conflicts in 25/26 files due to complex episode mapping
- Marked as `@pytest.mark.slow` for selective execution
- Validates volume-dependent edge cases missed by sampling

**Why Both Approaches Matter:**

The sampling approach initially missed **volume-dependent mapping conflicts** that only surface when processing complete directories. For example, Paw Patrol has complex mapping where:
- `Paw Patrol-S01E01-*.mp4` → actual episodes S01E05-E06 (not S01E01-E02)  
- File numbering sequence doesn't match canonical TVDB episode sequence
- Multiple files can map to overlapping episode ranges, causing conflicts

**Volume testing successfully detected these conflicts** in 25/26 Season 1 files, proving the need for both testing approaches.

### Volume Testing (TestVolumeEndToEnd)

**Purpose:** Detect edge cases that only emerge when processing complete show directories across all 6 hand-selected shows.

**Comprehensive Volume Tests:**
1. **`test_paw_patrol_full_volume_mapping_conflicts`** - Complex episode mapping conflicts (Season 1, 26 files)
2. **`test_harvey_girls_forever_volume_untrusted_names`** - Untrusted names with special character handling at scale
3. **`test_martha_speaks_volume_apostrophe_edge_cases`** - Apostrophe normalization and same-name episodes across seasons
4. **`test_octonauts_volume_title_disambiguation`** - Show name normalization consistency ("The Octonauts" vs "Octonauts")
5. **`test_firebuds_volume_trusted_titles_validation`** - Trusted title assumption validation at scale
6. **`test_danger_mouse_volume_non_anthology_control`** - Non-anthology processing consistency control case
7. **`test_all_shows_comprehensive_volume_testing`** - Cross-show volume conflict detection when processing all 6 together

**Performance:** Volume tests are marked `@pytest.mark.slow` and can be run selectively:

```bash
# Run only volume tests
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/ -m "slow" -v

# Skip volume tests  
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/ -m "not slow" -v
```

**Why Volume Testing All Shows Is Essential:**

Each of the 6 shows was **hand-selected for specific edge cases** that require full directory validation:

| Show | Edge Case Focus | Volume Issue Detection |
|------|----------------|----------------------|
| **Paw Patrol** | Complex mapping conflicts | File sequence ≠ canonical episode order, overlap detection |
| **Harvey Girls Forever!** | Untrusted names, special characters | SONARR-style handling, punctuation preservation at scale |
| **Martha Speaks** | Apostrophes, same-name episodes | Title normalization, cross-season disambiguation |
| **The Octonauts** | Title disambiguation | "The Octonauts" vs "Octonauts" consistency across many files |
| **Firebuds** | Trusted title validation | High auto-success rate validation at scale, edge case detection |
| **Danger Mouse 2015** | Non-anthology control | Consistent non-anthology processing validation |
| **Cross-Show Testing** | Volume conflicts | Destination conflicts between different show types |

**Expected Output:** Volume tests document any conflicts found:
```
Volume testing found mapping conflicts in: [list of conflicting files]
Harvey Girls Forever volume testing found untrusted name conflicts: [list]
Martha Speaks volume testing found same-name episode conflicts: [list]
```

### Running Anthology Show Tests

```bash
# All anthology tests (sampling + volume)
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/test_real_tv_scan.py::TestAnthologyShowsEndToEnd -v
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/test_real_tv_scan.py::TestVolumeEndToEnd -v

# Specific show testing
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/test_real_tv_scan.py::TestAnthologyShowsEndToEnd::test_anthology_show_specific_edge_cases[Paw\ Patrol-*] -v

# Fast sampling tests only  
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/test_real_tv_scan.py::TestAnthologyShowsEndToEnd -m "not slow" -v

# Volume tests only (all 7 comprehensive volume tests)
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/test_real_tv_scan.py::TestVolumeEndToEnd -m "slow" -v

# Individual show volume tests
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/test_real_tv_scan.py::TestVolumeEndToEnd::test_paw_patrol_full_volume_mapping_conflicts -v
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/test_real_tv_scan.py::TestVolumeEndToEnd::test_harvey_girls_forever_volume_untrusted_names -v
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/test_real_tv_scan.py::TestVolumeEndToEnd::test_martha_speaks_volume_apostrophe_edge_cases -v
```

## Test Markers

Tests are marked for selective execution:

- `@pytest.mark.e2e` - Core E2E tests (no external dependencies)
- `@pytest.mark.api` - Tests requiring API keys
- `@pytest.mark.llm` - Tests requiring Ollama

## Quick Start

### Enable E2E Testing

```bash
export NAMEGNOME_E2E_TESTS=1
```

### Run All E2E Tests

```bash
# Run all E2E tests (16 tests total)
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/ -v

# Run only Core E2E (no external dependencies)
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/ -m "e2e and not api and not llm" -v

# Run only anthology show coverage tests  
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/test_real_tv_scan.py::TestAnthologyShowsEndToEnd -v
```

## Dependency-Specific Testing

### Core E2E (No Dependencies Required)

```bash
# These always run - no external dependencies needed
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/ -m "e2e and not api and not llm" -v
```

Uses cached API responses and deterministic LLM for 100% reproducible results.

### API E2E (Requires API Keys)

```bash
# Run API E2E (requires API keys)
export TVDB_API_KEY="your_tvdb_key"  # pragma: allowlist secret
export TMDB_API_KEY="your_tmdb_key"  # pragma: allowlist secret
export OMDB_API_KEY="your_omdb_key"  # pragma: allowlist secret

NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/ -m "api and not llm" -v
```

### LLM E2E (Requires Ollama)

```bash
# Ensure Ollama is running with a model
ollama run llama3.2:3b  # or your preferred model

# Run LLM E2E
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/ -m "llm and not api" -v
```

### Full E2E (Requires Both)

```bash
# Run with API keys
NAMEGNOME_E2E_TESTS=1 TVDB_API_KEY="key" poetry run pytest tests/e2e/ -m "api and not llm" -v  # pragma: allowlist secret

# Run with Ollama  
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/ -m "llm and not api" -v

# Run with both (complete pipeline)
NAMEGNOME_E2E_TESTS=1 TVDB_API_KEY="key" poetry run pytest tests/e2e/ -m "api and llm" -v  # pragma: allowlist secret
```

## Test Coverage Details

### Core Pipeline Tests (8 tests)

1. **Scan→Apply→Undo Cycle**: Complete file operation lifecycle
2. **Visual Elements**: Banner, gnomes, progress indicators  
3. **Real TVDB Integration**: Provider API connectivity
4. **Provider Fallback**: TVDB→TMDB→OMDb→AniList chain
5. **Real Ollama Integration**: LLM provider connectivity
6. **Confidence Thresholds**: Auto/manual/unsupported decisions
7. **Complete Pipeline**: Real APIs + real LLM integration
8. **Series Disambiguation**: Multiple series handling

### Anthology Show Tests (8 tests)

1. **Comprehensive Coverage**: All 6 show types in single test (~14 files)
2. **Show-Specific Edge Cases**: Parametrized by show type (6 variants)  
3. **Anthology vs Non-Anthology**: Behavior comparison test

#### Show-Specific Edge Cases Covered

- **Danger Mouse 2015**: Standard non-anthology processing
- **Firebuds**: `--anthology` flag with trusted episode titles
- **Harvey Girls Forever**: `--anthology --untrusted-titles` for Sonarr-style naming
- **Martha Speaks**: Apostrophe sanitization and same-name episode handling
- **Paw Patrol**: `--anthology --max-duration 25` for complex episode mapping
- **The Octonauts**: Title disambiguation ("The Octonauts" vs "Octonauts")

## Performance Characteristics

- **Individual tests**: Complete in <30 seconds each
- **Complete E2E suite**: ~60 seconds for all 16 tests
- **Core E2E only**: ~20 seconds for dependency-free tests
- **Anthology coverage**: ~20 seconds for all 6 show types

## Troubleshooting

### Common Issues

#### Test Skips

```bash
# If you see: "Test requires API keys"
export TVDB_API_KEY="your_key_here"  # pragma: allowlist secret

# If you see: "Test requires running Ollama instance"  
ollama serve
ollama run llama3.2:3b
```

#### Anthology-Specific Issues

```bash
# If anthology tests fail with "No test files found"
# Check that fixture files exist:
ls tests/mocks/tv/Firebuds/
ls tests/mocks/tv/"Harvey Girls Forever"/
ls tests/mocks/tv/"Martha Speaks"/
ls tests/mocks/tv/"Paw Patrol"/
ls tests/mocks/tv/"The Octonauts"/

# If anthology CLI flags are rejected:
poetry run python -m namegnome scan --help | grep -A5 anthology
```

#### Performance Issues

```bash
# If tests timeout (>30s), run with debugging:
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/ -v -s --tb=short

# Check for network connectivity issues:
curl -I https://api.thetvdb.com/
ping localhost # for Ollama connectivity
```

### Debugging Commands

```bash
# Test specific show type
NAMEGNOME_E2E_TESTS=1 poetry run pytest tests/e2e/test_real_tv_scan.py::TestAnthologyShowsEndToEnd::test_anthology_show_specific_edge_cases[Firebuds-expected_characteristics1] -v -s

# Test with real CLI (manual debugging)
poetry run python -m namegnome scan --media-type tv --anthology tests/mocks/tv/Firebuds/

# Validate fixture availability
poetry run python -c "
from pathlib import Path
mocks = Path('tests/mocks/tv')
for show in ['Danger Mouse 2015', 'Firebuds', 'Harvey Girls Forever', 'Martha Speaks', 'Paw Patrol', 'The Octonauts']:
    show_dir = mocks / show
    if show_dir.exists():
        files = list(show_dir.glob('*.mp4')) + list(show_dir.glob('*.mkv'))
        print(f'{show}: {len(files)} files')
    else:
        print(f'{show}: MISSING')
"
```

## CI Integration

E2E tests integrate with GitHub Actions:

- **Core E2E**: Run on every PR (no external dependencies)
- **Extended E2E**: Run nightly with available API keys and Ollama
- **Anthology Coverage**: Included in both workflows

See `.github/workflows/e2e.yml` for configuration details.

## Contributing

### Adding New Anthology Shows

To add coverage for a new anthology show:

1. Add test files to `tests/mocks/tv/Your Show Name/`
2. Update `tests/e2e/conftest.py::e2e_anthology_test_files` with representative samples
3. Add parametrized test case to `test_anthology_show_specific_edge_cases`
4. Document unique edge cases in this guide

### Extending Test Coverage

- Use `@pytest.mark.e2e` for Core E2E tests (no dependencies)
- Use `@pytest.mark.api` for tests requiring API keys
- Use `@pytest.mark.llm` for tests requiring Ollama  
- Ensure individual tests complete <30 seconds
- Follow the pattern of existing tests for consistency 