# Changelog

All notable changes to the namegnome project will be documented in this file.

## [Unreleased]

### Added
- Rich diff renderer with color-coded status indicators and progress spinners
- Custom DateTimeEncoder for proper JSON serialization of datetime objects
- Support for --no-color flag to disable ANSI color codes
- Comprehensive test suite for console output capture and validation
- Tests for color stripping in no-color mode
- Tests for JSON output format and validation
- Rename Planner module for generating conflict-aware rename plans
- Support for serializing rename plans to JSON with datetime handling
- Conflict detection for files targeting the same destination
- Tests for plan creation, conflict detection, and JSON serialization
- Directory Scanner module for scanning file systems for media files
- Support for detecting different media types (TV, Movies, Music)
- Tests for media file detection including non-ASCII filenames and hidden files
- Proper Python path configuration in conftest.py for consistent test execution
- Cleaned up project structure by removing duplicate directories
- Added case-insensitive conflict detection in the rename planner for cross-platform compatibility
- Implemented CLI scan command with plan storage to .namegnome directory
- Added support for various media type filtering options in scan command
- Created ScanOptions and ScanCommandOptions data models for better parameter organization
- Implemented detailed output formatting for scan results with rich tables
- UUID-based plan storage with SHA-256 checksums for file integrity verification
- Run metadata storage in YAML format for command tracking and reproducibility
- Plan store module for saving and retrieving rename plans
- Automatic creation of .namegnome/plans directory structure
- Backward compatibility with timestamp-based plan IDs
- README header image for improved project presentation
- Custom pre-commit hook (windows-compat-check) and supporting script to detect and block Windows-incompatible patterns (e.g., /tmp, os.path, backslashes, Windows drive letters) in Python files before commit. Helps prevent CI failures on Windows runners by catching issues early.
- 0.12 Docs Update: Expanded README (install, usage, roadmap), added architecture diagram under docs/, created CONTRIBUTING.md with commit style guidelines, added CI and coverage badges, and performed a full documentation and comment sweep for all modules (Google-style docstrings, inline reasoning comments, E501 compliance). Confirmed all docs pass markdown-lint and render on GitHub.
- Implemented and fully tested atomic_move with cross-platform, cross-device, dry-run, and overwrite logic. Added comprehensive documentation, usage examples, and advanced usage doc. Updated README and CONTRIBUTING.md. All tests pass and docs are E501-compliant.
- Implementation and testing of transactional apply engine (apply_plan) with rollback, hash verification, skip-identical logic, and status updates (Sprint 1.3).
- Undo engine and Typer CLI command with confirmation prompt, plan ID autocompletion, error handling for source/destination conflicts, and multi-file support (Sprint 1.4).
- Rich progress bars, spinners, and structured logging integrated into all CLI workflows (Sprint 1.5).
- End-to-end integration tests for multi-file undo, error cases, and CLI flows, running on all supported OSes in CI (Sprint 1.6).
- Created and cross-linked showcase-quality documentation: fs-operations.md, apply-undo.md, hashing.md, progress-logging.md, integration-testing.md, cli-commands.md.
- Updated README.md to add a '📚 Documentation' section with links to all new docs and reflect expanded documentation.
- Visual demo (GIF) of progress/rollback is planned for Sprint 2+ when real metadata is available.
- Sprint 2.1: Provider Abstraction Interface. Implemented MetadataClient ABC in src/namegnome/metadata/base.py with async search and details methods, using existing MediaMetadata model. Added TDD tests in tests/metadata/test_base.py for expected, edge, and failure cases. All code is E501/Google docstring compliant and passes all tests.
- Implemented TVDBClient with async search and details for TV series, including:
  - Authentication and token refresh logic
  - Series search and details endpoints
  - Paginated episode fetching
  - Mapping to MediaMetadata model
  - TDD tests for expected, edge, failure, pagination, and token refresh cases
- All requirements for Sprint 2.3 met.
- MusicBrainz client: async album/track metadata lookup, 1 req/sec rate limiting, custom User-Agent, TDD, and full API compliance. All edge/failure cases tested. README updated with provider compliance and attribution.
- TMDB client: async search/details, mapped to MediaMetadata, README updated with compliance attribution.
- TVDB client: async search/details, mapped to MediaMetadata, README updated with required attribution (logo, text, link) per TheTVDB API requirements.
- Provider abstraction interface for metadata clients (TMDB, TVDB, MusicBrainz).
- Metadata integration and tests for all providers.
- README updates: provider compliance, attribution, and usage examples for music/album/track.
- Attribution section in README with logos and links for TheTVDB, TMDB, and MusicBrainz.
- Implemented OMDb client to supplement TMDB with IMDb rating and full plot, with TMDB fields taking priority. OMDb API key loaded from environment, never hard-coded. Merge logic and TDD tests implemented. Integrated into TMDBClient.details for movies. (Sprint 2.5, 2025-05-13)
- Fanart.tv client for fetching and caching high-res artwork for movies by TMDB ID
- CLI --artwork flag to trigger artwork download and caching during scan
- TDD and integration tests for Fanart.tv client and CLI integration
- AniList GraphQL client for anime metadata with absolute episode numbering support
- Mapping of AniList streaming episodes to TVEpisode objects with absolute numbering
- TDD tests for AniList search, details, and error handling
- SQLite-backed local cache layer for metadata providers (Sprint 2.9)
  - Added src/namegnome/metadata/cache.py with SQLite table for provider, key_hash, json_blob, expires_ts
  - Implemented @cache(ttl=86400) decorator for async provider methods
  - Added CLI --no-cache flag to bypass cache for fresh API calls
  - Integrated cache with TMDBClient.search and tested expiry, bypass, and correctness
  - 100% test coverage for cache module and CLI flag
- Rule engine integration (Sprint 2.10, 2025-07-27): Naming rules now use provider metadata (e.g., movie year, TV episode title) for more accurate and platform-compliant renaming. All tests pass.
- Sprint 2.12: Implemented Settings class with pydantic, config CLI command, and robust error handling for missing API keys. All requirements and tests pass.
- Sprint 2.13 Docs Update: Created docs/providers.md with provider table, .env.example template (TDD enforced), and updated README.md with provider key setup instructions. All requirements and tests pass.
- Implemented async Ollama wrapper module (Sprint 3.1):
  - Added src/namegnome/llm/ollama_client.py with async generate() interface to local Ollama server
  - Full TDD: expected, edge, and failure tests (streaming, connection error, empty response)
  - Custom LLMUnavailableError for connection issues
  - E501 and type annotation compliance throughout
  - Project memory updated per Anthropic Memory MPC rules
- Async Ollama model discovery (`list_models`) in `ollama_client.py`
- CLI `llm` command group: `list` and `set-default` subcommands
- Config persistence for default LLM model (TOML config)
- Subprocess-based CLI tests for Typer global options (robust to Typer quirks)
- All requirements and tests for Sprint 3.2 pass as of 2025-07-27

### Fixed
- Fixed test failures related to console output capture
- Fixed JSON serialization issues with datetime objects
- Fixed media type detection to properly classify movies with year patterns
- Improved TV show pattern detection with better regex boundaries
- Enhanced directory walking logic with better error handling
- Fixed test failures caused by incorrect media type classification
- Fixed Python path configuration to ensure consistent test execution
- Removed duplicate test directories causing import conflicts
- Fixed project structure to follow best practices
- Fixed Ruff configuration by moving it from .ruff.toml to pyproject.toml section
- Fixed indentation error in PlexRuleSet for TV show pattern matching
- Fixed mypy type annotations in Pattern objects to use Pattern[str]
- Added missing Generator type annotations in test fixtures
- Fixed scanner module complexity by refactoring directory processing into smaller functions
- Fixed ScanResult model to maintain backward compatibility with older tests
- Fixed parameter naming inconsistencies in scan_directory function
- Fixed serialization of Path objects in YAML files
- Corrected handling of Enum values in YAML serialization
- Fixed path handling in file checksums computation
- Fixed Enum comparison bug in CLI scan command that prevented artwork logic from triggering for movie files

### Changed
- Refactored scan command and CLI error handling for proper exit codes and user-facing output.
- Updated all tests to assert on real CLI output and exit codes.
- Removed all skipped/redundant tests; all tests now pass with zero skips.
- Migrated to Pydantic v2 ConfigDict to resolve deprecation warnings.
- Ensured full cross-platform CI compatibility and green pipeline.
- Roadmap and Completed sections in README and TASK.md now reflect all Sprint 2 features as completed and documented.

## [0.2.1] - 2025-05-10

### Added
- Fixed metadata client tests and type annotations
- Added missing Any import to metadata models
- Fixed fixture file loading path
- Removed duplicate tests directory from root level

### Fixed
- Corrected fixture file path resolution in metadata utils
- Added proper type annotation for kwargs in metadata client factory function
- Removed unnecessary type ignore comment

## [0.2.0] - 2025-05-05

### Added
- Created proper package structure with all required modules
- Added models directory for upcoming domain models
- Implemented CLI module with Typer app and version command
- Made package executable via `python -m namegnome`
- Fixed import structure for better maintainability
- Implemented domain models using Pydantic v2 with comprehensive testing
- Implemented Rule Engine with abstract RuleSet and Plex naming rules
- Added regex-based filename parsing for TV shows and movies
- Fixed CI pipeline with improved configuration and type annotation fixes
- Added metadata API client abstraction layer with TMDB and TVDB stubs
- Implemented MediaMetadata model for normalized provider data
- Created fixture-based metadata clients for testing without network calls

### Fixed
- Resolved cross-platform formatting issues in the CI pipeline
- Added proper type annotations for Typer and pytest decorators
- Ensured consistent line endings with .gitattributes
- Fixed ruff configuration to work correctly in pre-commit hooks
- Restructured pre-commit hooks to prevent conflicts between formatters

## [0.1.0] - 2025-05-05

### Added
- Initialized project with Hatch, set up Python 3.12 support
- Created directory structure following project architecture guidelines
- Set up development dependencies in pyproject.toml
- Configured pre-commit hooks (ruff-format, black, ruff, mypy, pytest)
- Added GitHub Actions CI workflow for multi-OS testing
- Created basic CLI module with Typer app object
- Established Git workflow with main and develop branches
- Added basic test for version verification

### Infrastructure
- Set up GitHub repository with branch protection
- Implemented Git branching strategy (develop for work, main for stable releases)
- Configured editor settings for consistent development 

## [0.2.2] - 2024-05-12

### Added
- SHA-256 hash utility for file integrity, integrated with scan and apply workflows; comprehensive tests for all hash scenarios.
- Transactional apply engine with hash verification, rollback on failure, skip-identical logic, and robust error handling. Fully tested with unit and CLI tests.
- Undo engine and Typer CLI command with confirmation prompt, plan ID autocompletion, error handling for source/destination conflicts, and multi-file support. Fully tested with unit, CLI, and integration tests.
- Rich progress bars and per-file logging to undo CLI, matching scan/apply UX. All operations are logged and user-visible.
- End-to-end integration tests for multi-file undo, error cases, and CLI flows. Ensured all practical user scenarios are covered.
- Updated README.md with undo command usage, error handling, and multi-file examples. Performed a full documentation and comment sweep for all modules, ensuring Google-style docstrings, inline reasoning comments, and E501 compliance. All docs pass markdown-lint and render correctly on GitHub.

### Fixed
- Corrected fixture file path resolution in metadata utils
- Added proper type annotation for kwargs in metadata client factory function
- Removed unnecessary type ignore comment

### Changed
- Refactored scan command and CLI error handling for proper exit codes and user-facing output.
- Updated all tests to assert on real CLI output and exit codes.
- Removed all skipped/redundant tests; all tests now pass with zero skips.
- Migrated to Pydantic v2 ConfigDict to resolve deprecation warnings.
- Ensured full cross-platform CI compatibility and green pipeline. 

### Sprint 2.8: TheAudioDB Client (2025-07-27)
- Implemented async TheAudioDB client for artist and album lookup, including:
  - Artist search via theaudiodb.com API (dev key "2")
  - Album lookup and thumbnail download (artwork saved to disk)
  - Updates MediaMetadata.artwork list with downloaded images
  - TDD: expected-flow, edge, and file I/O tests (artist not found, album thumb download)
- All requirements and tests pass.

## [2.11] - 2025-07-27
### Added
- Parametrized, fixture-based tests for all metadata providers (TMDB, TVDB, MusicBrainz, OMDb, Fanart.tv, TheAudioDB, AniList)
- Coverage for expected, 404 (not found), and 429 (rate-limit) error cases
- All tests pass and coverage ≥85% for metadata package
- Implementation updated to raise on 429 and handle 404 consistently across all providers
- Fully compliant with project TDD and coverage requirements 