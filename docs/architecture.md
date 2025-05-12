# NameGnome Architecture

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

## Component Overview

- **CLI (Typer/Rich):** User interface for all commands, output, and progress.
- **Core Renamer Engine:** Handles validation, planning, and transformation of file names and paths.
- **TMDB API / TVDB API / MusicBrainz:** Metadata providers for movies, TV, and music.
- **LLM Agent:** Handles fuzzy matching, anthology logic, and edge-case reasoning (via Ollama).
- **Rollback:** Stores pre-flight plans and manages atomic, reversible file operations.

See `PLANNING.md` for more details on architecture and design decisions. 