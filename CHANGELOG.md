# Changelog

All notable changes to the namegnome project will be documented in this file.

## [Unreleased]

## [0.1.0] - 2024-11-27

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