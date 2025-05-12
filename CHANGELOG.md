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

### Changed
- Refactored scan command and CLI error handling for proper exit codes and user-facing output.
- Updated all tests to assert on real CLI output and exit codes.
- Removed all skipped/redundant tests; all tests now pass with zero skips.
- Migrated to Pydantic v2 ConfigDict to resolve deprecation warnings.
- Ensured full cross-platform CI compatibility and green pipeline.

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