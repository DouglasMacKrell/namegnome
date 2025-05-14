![NameGnome](public/images/NameGnome_README_Headder.png)

[![CI](https://github.com/DouglasMacKrell/namegnome/actions/workflows/ci.yml/badge.svg)](https://github.com/DouglasMacKrell/namegnome/actions)
[![Coverage Status](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://github.com/yourusername/namegnome)

See [docs/architecture.md](docs/architecture.md) for a full architecture diagram.

# NameGnome

A command-line tool for organizing and renaming media files according to platform-specific conventions (e.g., Plex, Jellyfin).

## 📚 Documentation

- [**Architecture Overview**](docs/architecture.md): High-level design and component diagram.
- [**Filesystem Operations**](docs/fs-operations.md): Atomic, cross-platform file moves and guarantees.
- [**Apply & Undo Engines**](docs/apply-undo.md): Transactional renaming, rollback, and CLI/Python usage.
- [**Hashing & Integrity**](docs/hashing.md): SHA-256 utility, integrity checks, and skip-identical logic.
- [**Progress Bars & Logging**](docs/progress-logging.md): Rich CLI UX, progress bars, spinners, and audit logging.
- [**Integration Testing**](docs/integration-testing.md): End-to-end test philosophy, structure, and guarantees.
- [**CLI Command Reference**](docs/cli-commands.md): All commands, flags, usage, exit codes, and advanced options.

## Features

- Scan directories for media files
- Support for TV shows, movies, and music (album/track)
- Platform-specific naming conventions
- Multi-segment episode handling
- Explicit media information control
- JSON output support
- File integrity verification (SHA-256)
- **Apply & Undo engine**: Transactional, reversible renames
- **Rich progress bars & logging**: CLI feedback and audit trail
- **Integration tests**: End-to-end, cross-platform
- **Pluggable metadata/artwork providers**: TMDB, TVDB, MusicBrainz, Fanart.tv, TheAudioDB (API compliant)

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
│   ├── fs-operations.md
│   ├── apply-undo.md
│   ├── hashing.md
│   ├── progress-logging.md
│   ├── integration-testing.md
│   ├── cli-commands.md
│   └── architecture.md
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
- `--artwork`: Download and cache high-quality poster artwork for each movie using
  Fanart.tv (requires FANARTTV_API_KEY in your .env)

### Music Options
- `--media-type music`: Scan and organize music files (albums/tracks)

### Output & Verification
- `--json`: Output results as JSON
- `--no-color`: Disable colored output (for logs/CI)
- `--verify`: Compute and store SHA-256 checksums for file integrity
- `--llm-model "model-name"`: Use a specific LLM for fuzzy matching

### Apply and Undo
Apply a saved rename plan:
```bash
namegnome apply <plan-id>
```
Undo a previous operation:
```bash
namegnome undo <plan-id>
```

### Music Metadata Lookup
- Music files are matched using MusicBrainz (API compliant: 1 req/sec, custom User-Agent)
- Example:
```bash
namegnome scan /media/Music --media-type music
```

## Undo Command

The `undo` command reverts a previously executed rename plan, restoring all files to their original locations. It supports multi-file undo, robust error handling, and a confirmation prompt for safety.

### Usage

```sh
namegnome undo <plan-id> [--yes]
```

- `<plan-id>`: The ID of the plan to undo (autocompletes from available plans).
- `--yes`: Skip confirmation prompt and undo immediately.

### Example

```sh
namegnome undo 123e4567-e89b-12d3-a456-426614174000
```

You will be prompted for confirmation unless you pass `--yes`:

```sh
Are you sure you want to undo the plan 123e4567-e89b-12d3-a456-426614174000? [y/N]: y
Restoring /path/to/moved1.txt -> /path/to/original1.txt
Restoring /path/to/moved2.txt -> /path/to/original2.txt
[green]Undo completed for plan: 123e4567-e89b-12d3-a456-426614174000[/green]
```

### Error Handling

- If the original source file already exists, undo will fail and not overwrite:
  ```sh
  [red]Cannot restore: source file already exists: /path/to/original1.txt[/red]
  ```
- If the destination file is missing (already undone), undo will fail:
  ```sh
  [red]Cannot restore: destination file does not exist: /path/to/moved1.txt[/red]
  ```

### Multi-file Undo

The undo command restores all files in the plan. Each file is logged as it is restored. Progress is shown with a spinner.

## Technology Stack

- **Python 3.12+**: Modern language features and performance
- **Typer**: Declarative CLI framework
- **Rich**: Beautiful CLI output (tables, spinners, progress bars)
- **Pydantic v2**: Data validation and serialization
- **httpx + asyncio**: Async HTTP for metadata providers
- **TMDB, TVDB, MusicBrainz API clients**: async, rate-limited, custom User-Agent
- **pytest**: Testing framework (80%+ coverage enforced)
- **black, ruff, mypy**: Formatting, linting, and static typing
- **Ollama**: Local LLM server for fuzzy matching and edge-case handling

## Metadata Providers

NameGnome supports pluggable metadata providers:
- **TMDB**: Movies and TV metadata
- **TVDB**: TV episode and series metadata
- **MusicBrainz**: Music album/track/artist metadata
  - Fully compliant with [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API):
    - 1 request/sec rate limiting
    - Custom User-Agent header
- **OMDb**: Supplements TMDB with IMDb rating and full plot. Requires a free or patron API key (see [OMDb API](https://www.omdbapi.com/)). Free keys are limited to 1,000 requests/day. OMDb fields are only used if missing from TMDB, and TMDB always takes priority.
- **Fanart.tv**: High-quality poster artwork for movies (by TMDB ID). Requires a free
  API key (see [Fanart.tv API](https://fanart.tv/api-docs/)). Artwork is downloaded
  and cached locally when the `--artwork` flag is used.
- **AniList**: Anime metadata with absolute episode numbering support. Uses AniList's GraphQL API
  which does not require authentication.

## OMDb API Key Setup

- Register for a free OMDb API key at [omdbapi.com](https://www.omdbapi.com/apikey.aspx).
- Add `OMDB_API_KEY` to your `.env` file (never hard-code keys).
- If the key is missing, OMDb supplementation will be skipped.

## Fanart.tv API Key Setup

- Register for a free Fanart.tv API key at [fanart.tv/api](https://fanart.tv/api/).
- Add `FANARTTV_API_KEY` to your `.env` file (never hard-code keys).
- If the key is missing, the `--artwork` flag will be ignored and no artwork will be
  downloaded.

## Attribution

<p align="center">
  <a href="https://thetvdb.com">
    <img src="https://thetvdb.com/images/logo.png" alt="TheTVDB Logo" width="120"/>
  </a><br>
  Metadata provided by <a href="https://thetvdb.com">TheTVDB</a>.<br>
  Please consider adding missing information or subscribing.
</p>

<p align="center">
  <a href="https://www.themoviedb.org/">
    <img src="https://www.themoviedb.org/assets/2/v4/logos/stacked-blue-3c3c3c3c.png" alt="TMDB Logo" width="120"/>
  </a><br>
  This product uses the TMDB API but is not endorsed or certified by TMDB.<br>
  <a href="https://www.themoviedb.org/documentation/api/terms-of-use">TMDB API Terms of Use</a>
</p>

<p align="center">
  <a href="https://musicbrainz.org/">
    <img src="https://musicbrainz.org/static/images/entity-header-logo.svg" alt="MusicBrainz Logo" width="120"/>
  </a><br>
  Music metadata provided by <a href="https://musicbrainz.org/">MusicBrainz</a>.
</p>

<p align="center">
  <a href="https://www.omdbapi.com/">
    <img src="https://www.omdbapi.com/favicon.ico" alt="OMDb Logo" width="32"/>
  </a><br>
  Movie metadata supplemented by <a href="https://www.omdbapi.com/">OMDb API</a>.<br>
  <a href="https://www.omdbapi.com/legal.htm">OMDb API Terms of Use</a>
</p>

<p align="center">
  <a href="https://fanart.tv/">
    <img src="https://assets.fanart.tv/fanarttv-logo.svg" alt="Fanart.tv Logo" width="120"/>
  </a><br>
  Artwork provided by <a href="https://fanart.tv/">Fanart.tv</a>.<br>
  <a href="https://fanart.tv/terms/">Fanart.tv API Terms of Use</a>
</p>

<p align="center">
  <a href="https://anilist.co/">
    <img src="https://anilist.co/img/icons/icon.svg" alt="AniList Logo" width="32"/>
  </a><br>
  Anime metadata provided by <a href="https://anilist.co/">AniList</a>.<br>
  <a href="https://anilist.gitbook.io/anilist-apiv2-docs/">AniList GraphQL API</a>
</p>

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

## Advanced: Atomic & Cross-Platform File Moves

NameGnome uses a robust, cross-platform atomic move engine for all file
renaming and reorganization. This ensures:

- Safe, auditable, and reversible moves—even across devices or on Windows with
  long paths.
- Overwrite protection, dry-run support, and byte-for-byte duplicate detection.

See the full API, advanced usage, and guarantees in  
[`docs/fs-operations.md`](docs/fs-operations.md).

## Roadmap / Completed

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

### Sprint 2 (MVP 0.3 "Metadata APIs")
- Provider abstraction interface
- TMDB client (movies/TV)
- TVDB client (TV)
- MusicBrainz client (music, API compliant)
- Metadata integration and tests
- Coverage and compliance improvements
- OMDb client (supplemental movie metadata)
- Fanart.tv client (high-quality poster artwork, CLI --artwork flag, caching) 