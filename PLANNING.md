# NameGnome v1 — PLANNING.md

> **Keep this file open in every conversation. Prompt to AI:** *"Use the structure and decisions outlined in PLANNING.md."*

---

## 1 · Purpose & Vision

NameGnome v1 is a local‑first CLI (MVP) and optional GUI application that **analyzes, renames and reorganizes media files so they ingest flawlessly into self‑hosted media servers (Plex, Jellyfin, Emby, Navidrome, etc.)**.  It leverages modern LLMs (via Ollama) plus canonical metadata APIs to handle fuzzy matches, anthology logic, absolute numbering, multi‑edition movies, and music tag repair—all with a one‑command rollback safety net.

### High‑level goals

* **Zero‑click happy‑path** – a single command can lint a directory, show a dry‑run plan, then apply changes.
* **Pluggable back ends** – add or swap metadata providers (TMDB, TVDB, MusicBrainz, Fanart.tv) without touching the renamer core.
* **Deterministic & reversible** – every operation is logged; `namegnome undo <ID>` reverts a batch.
* **Extensible UI** – the CLI drives everything; a Next.js + Styled‑Components GUI wraps the same API in v2.

---

## 2 · Architecture Overview

```
┌────────────────────────┐      ┌───────────────────────┐
│    CLI (Typer/Rich)    │──────│  Core Renamer Engine   │
└────────────────────────┘      └───────────────────────┘
                                        │
       ┌──────────────┬──────────────────┼──────────────────┬──────────────┐
       │              │                  │                  │              │
┌────────────┐ ┌────────────┐   ┌──────────────┐   ┌────────────┐   ┌────────────┐
│ TMDB API   │ │  TVDB API  │   │ MusicBrainz  │   │  LLM Agent │   │  Rollback  │
└────────────┘ └────────────┘   └──────────────┘   └────────────┘   └────────────┘
```

### Project Structure

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
├── README.md          # Project overview
├── PLANNING.md        # Project planning and vision
└── TASK.md           # Current tasks and sprints
```

* **Core Renamer Engine** – pure‑Python library exposing validators, transformers and planners.
* **LLM Agent** – delegates fuzzy matching and edge‑case reasoning; default model *deepseek‑coder‑instruct‑1.5b* via Ollama, selectable via CLI flag.
* **Rollback module** – stores pre‑flight JSON plans and watches `os.rename()` calls; uses atomic moves where the FS allows.
* **Future GUI** – Next.js (App Router) talking to a local FastAPI served by the same Python package via `uvicorn`.

---

## 3 · Tech Stack & Conventions

| Area                    | Choice                                                                              | Rationale                                                   |
| ----------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **Language**            | Python ≥ 3.12                                                                       | Pattern‑matching & perf                                     |
| **CLI Framework**       | Typer                                                                               | Declarative commands & Click ecosystem                      |
| **CLI UX / Output**     | Rich                                                                                | Coloured tables, progress bars, spinners, pretty tracebacks |
| **Async HTTP**          | httpx + asyncio                                                                     | Concurrency with rate limits                                |
| **Validation**          | pydantic v2                                                                         | Typed models for API payloads & plans                       |
| **ORM / DB (optional)** | SQLModel + SQLite                                                                   | Persist scan history; lightweight                           |
| **Testing**             | Pytest                                                                              | Sole test runner; coverage 90 %+                            |
| **Formatting/Lint**     | black, ruff, mypy                                                                   | Consistency & static checks                                 |
| **Packaging**           | Hatchling + pipx                                                                    | Simple install; pyinstaller later                           |
| **LLM**                 | Ollama local server (default)                                                       | Offline inference, user‑switchable                          |
| **GUI**                 | Next.js 14 + Styled Components                                                      | Consistent theming, SSR                                     |
| **Naming rules source** | *Media Server File Naming Guide* (canvas doc ID `6818d51b4fc08191b5398af459d6f306`) | Single source of truth                                      |

### CLI UX Guidelines

* Use `rich.console.Console` for **all** user‑visible output; avoid raw `print`.
* Default commands detect non‑TTY and automatically downgrade to plain text (Rich does this).
* Show **status spinners** (`console.status`) around long‑running network or LLM requests.
* All file operations under `apply`/`undo` display a **progress bar** with percentage and ETA.
* Use **colour legend** in diff tables: green = move, yellow = new folder, red = conflict.
* Enable `rich.traceback.install(show_locals=True)` at startup for friendly crash reports.
* Provide a `--json` flag on `scan` and `apply` to emit machine‑readable output without ANSI codes.

### CLI Flag Requirements

Required flags:
* `root` (argument) - Root directory to scan for media files
* `--media-type`, `-t` - Media types to scan for (tv, movie, music). At least one type must be specified.

Optional flags with defaults:
* `--platform`, `-p` - Target platform (e.g., plex, jellyfin), defaults to "plex"
* `--show-name` - Explicit show name for TV files
* `--movie-year` - Explicit year for movie files
* `--anthology` - Whether the TV show is an anthology series (False)
* `--adjust-episodes` - Adjust episode numbering for incorrectly numbered files (False)
* `--verify` - Verify file integrity with checksums (False)
* `--json` - Output results in JSON format (False)
* `--llm-model` - LLM model to use for fuzzy matching
* `--no-color` - Disable colored output (False)
* `--strict-directory-structure` - Enforce platform directory structure (True)

Constraints:

* Entire codebase respects Cursor Rules (see `CURSOR_RULES.md`).
* No single file > 500 LOC; functional decomposition first.
* Must run on Windows, macOS, Linux; avoid platform‑specific paths.

---

## 4 · Key Features (MVP)

1. **`scan` command** – dry‑run analysis; outputs table of proposed renames and folder moves.
2. **`apply` command** – executes the current plan with progress bar & JSON log.
3. **`undo` command` – roll back last (or specific) transaction using saved plan.
4. **Platform presets & extensibility** – first‑class flags for

   * `plex`, `jellyfin`, `emby`, `navidrome`
   * plus video‑only presets: `kodi`, `olaris`, `streama`
   * lightweight/DLNA targets: `universal‑media‑server`, `gerbera`, `minidlna`
     Preset determines naming conventions, tag strategy, and which metadata providers are queried.  New servers can be added via a plug‑in folder without touching core code. **Media‑type handlers** – TV, Film, Music.  Anime flag enables absolute numbering heuristics.
5. **Fuzzy LLM assist** – resolves anthology splits, detects dual‑episode files, suggests provider IDs when ambiguous.
6. **Safety** – hash verification after move, skip duplicates unless `--force`.

---

## 5 · Phase 2 (Post‑MVP)

* **GUI front‑end** – file explorer, diff viewer, undo history.
* **Music tag editing** – integrate Mutagen or TinyTag to fix ID3/FLAC fields.
* **Rules engine** – user‑authored YAML templates for niche servers.
* **Docker & Homebrew releases**.

---

## 6 · Open Questions

* Best lightweight LLM for local semantic similarity on filenames (<8 GB VRAM)?
* Strategy for multi‑threaded FS ops without starving IO on network shares.
* MusicBrainz rate limiting—need user token or caching layer?

---

*Last reviewed: 2025‑05‑05*
