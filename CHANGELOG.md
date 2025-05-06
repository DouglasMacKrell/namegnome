# Changelog

All notable changes to the namegnome project will be documented in this file.

## [Unreleased]

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