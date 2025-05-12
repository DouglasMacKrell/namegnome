![NameGnome](public/images/NameGnome_README_Headder.png)

[![CI](https://github.com/yourusername/namegnome/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/namegnome/actions)
[![Coverage Status](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://github.com/yourusername/namegnome)

See [docs/architecture.md](docs/architecture.md) for a full architecture diagram.

# NameGnome

A command-line tool for organizing and renaming media files according to platform-specific conventions (e.g., Plex, Jellyfin).

## Features

- Scan directories for media files
- Support for TV shows and movies
- Platform-specific naming conventions
- Multi-segment episode handling
- Explicit media information control
- JSON output support
- File integrity verification

## Project Structure

```
namegnome/                  # Project root
├── src/                   # Source code directory
│   └── namegnome/        # Package directory
│       ├── cli/         # CLI commands and UI
│       ├── core/        # Core renaming engine
│       ├── rules/       # Platform-specific rules
│       ├── metadata/    # Metadata providers
│       ├── fs/          # Filesystem operations
│       └── prompts/     # LLM prompt templates
├── tests/               # Test directory (mirrors src structure)
├── docs/               # Documentation
│   └── ADR-*.md       # Architecture Decision Records
├── config/            # Configuration files and scripts
│   └── scripts/       # Development and utility scripts
├── README.md          # Project overview
├── PLANNING.md        # Project planning and vision
└── TASK.md           # Current tasks and sprints
```

## Installation

### Prerequisites
- **Python**: 3.12 or higher
- **Supported OS**: Windows, macOS, Linux (cross-platform tested)
- **Recommended**: [pipx](https://pypa.github.io/pipx/) for isolated CLI installs

### Install via pip
```bash
pip install namegnome
```

### Install via pipx (recommended)
```bash
pipx install namegnome
```

### Verify installation
```bash
namegnome --help
```

## Project Highlights

- **Zero-click happy-path**: Scan, preview, and rename in one command
- **Platform presets**: Out-of-the-box support for Plex, Jellyfin, Emby, Navidrome, and more
- **Fuzzy LLM assist**: Handles anthology episodes, ambiguous titles, and edge cases using local LLMs (Ollama)
- **Safe by default**: Dry-run planning, conflict detection, and one-command rollback
- **Rich CLI UX**: Colorful tables, progress bars, and spinners powered by Rich
- **Extensible**: Pluggable metadata providers and naming rules
- **Cross-platform**: Works on Windows, macOS, and Linux

## Usage

NameGnome is a CLI tool. All commands and options are available via `namegnome --help`.

### Basic Scan
Scan a directory for media files and preview the proposed renames:
```bash
namegnome scan /path/to/media/files
```

### Platform Selection
Choose a target platform to apply its naming conventions:
```bash
namegnome scan /path/to/media/files --platform plex
namegnome scan /path/to/media/files --platform jellyfin
```

### Media Type Filtering
Limit scan to specific media types:
```bash
# TV only
namegnome scan /path/to/media/files --media-type tv
# Movies only
namegnome scan /path/to/media/files --media-type movie
# Both
namegnome scan /path/to/media/files --media-type tv --media-type movie
```

### TV Show Options
- `--show-name "Show Title"`: Override detected show name
- `--anthology`: Handle multi-segment episodes (e.g., Paw Patrol)
- `--adjust-episodes`: Fix episode numbering if files are in correct order but misnumbered

### Movie Options
- `--movie-year 2023`: Specify release year for movie files

### Output & Verification
- `--json`: Output results as JSON
- `--no-color`: Disable colored output (for logs/CI)
- `--verify`: Compute and store SHA-256 checksums for file integrity
- `--llm-model "model-name"`: Use a specific LLM for fuzzy matching

### Apply and Undo (coming in Sprint 1)
- `namegnome apply <plan-id>`: Apply a saved rename plan
- `namegnome undo <plan-id>`: Roll back a previous operation

## Technology Stack

- **Python 3.12+**: Modern language features and performance
- **Typer**: Declarative CLI framework
- **Rich**: Beautiful CLI output (tables, spinners, progress bars)
- **Pydantic v2**: Data validation and serialization
- **httpx + asyncio**: Async HTTP for metadata providers
- **pytest**: Testing framework (80%+ coverage enforced)
- **black, ruff, mypy**: Formatting, linting, and static typing
- **Ollama**: Local LLM server for fuzzy matching and edge-case handling

## Examples

### Organizing a TV Show with Multi-Segment Episodes
```bash
namegnome scan /media/TV/PawPatrol \
  --show-name "Paw Patrol" \
  --anthology \
  --adjust-episodes
```

### Organizing Movies with Explicit Year
```bash
namegnome scan /media/Movies \
  --media-type movie \
  --movie-year 2023
```

### Complex Organization (Plex, TV + Movies, JSON output, verification)
```bash
namegnome scan /media/Library \
  --platform plex \
  --media-type tv \
  --media-type movie \
  --show-name "Paw Patrol" \
  --anthology \
  --adjust-episodes \
  --verify \
  --json
```

## Exit Codes
- `0`: Success (all files processed or nothing to do)
- `1`: Error (general failure)
- `2`: Manual intervention needed (conflicts or manual review required)

## Notes
- All rename operations require manual review by default
- The tool will detect and report conflicts in target paths
- File integrity verification is optional but recommended
- JSON output is useful for programmatic processing
- The `--anthology` flag is for shows with multiple segments per file
- The `--adjust-episodes` flag helps correct episode numbering when files are in the right order but numbered incorrectly

## Roadmap

### Sprint 0 (MVP 0.1 "Dry-Run Scanner")
- Project scaffolding, pre-commit, and CI setup
- Core package skeleton and CLI
- Domain models with Pydantic
- Rule engine prototype (Plex naming)
- Metadata provider stubs (TMDB, TVDB)
- Directory scanner for media files
- Rename planner with conflict detection
- Rich diff renderer and CLI UX
- CLI `scan` command
- Rollback plan store
- Test harness and baseline coverage
- Contributor and user documentation

### Sprint 1 (MVP 0.2 "Apply & Undo")
- Atomic, cross-platform file move helper
- SHA-256 hash utility for file integrity
- Apply engine for transactional renames
- Undo engine and CLI command
- Progress bars and logging
- Integration tests across OSes
- Expanded documentation 