# CLI Command Reference: NameGnome

This document provides a comprehensive reference for all NameGnome CLI
commands, flags, and options. Each command is documented with required and
optional arguments, usage examples, exit codes, and advanced usage tips.

## scan

Analyze a directory for media files and generate a rename plan.

### Usage

```sh
namegnome scan <root> [OPTIONS]
```

- `<root>`: Path to the directory to scan (required)

### Options

- `--platform, -p <platform>`: Target platform (plex, jellyfin, emby, navidrome, etc.)
  (default: plex)
- `--media-type, -t <type>`: Media types to scan for (tv, movie, music). Can be
  specified multiple times **(required—specify at least one)**.
- `--show-name <name>`: Override detected show name (TV only)
- `--movie-year <year>`: Specify release year for movie files
- `--anthology`: Handle multi-segment episodes (e.g., Paw Patrol)
- `--adjust-episodes`: Fix episode numbering if files are in correct order but
  misnumbered
- `--untrusted-titles`: Ignore filename titles and rely solely on canonical metadata (useful for low-quality rips)
- `--max-duration <minutes>`: Maximum episode duration when pairing anthology spans (pairs episodes whose combined duration ≤ limit)
- `--artwork`: Download and cache high-quality posters for movies during scan
- `--no-cache`: Bypass the SQLite metadata cache and force fresh provider look-ups
- `--verify`: Compute and store SHA-256 checksums for file integrity
- `--json`: Output results as JSON
- `--no-color`: Disable colored output (for logs/CI)
- `--no-rich`: Disable Rich spinners/progress bars and pretty tracebacks (falls back to plain `print`). Ideal for piping output or minimal terminals.
- `--llm-model <model>`: Use a specific LLM for fuzzy matching
- `--strict-directory-structure/--no-strict-directory-structure`: Enforce or
  relax platform directory structure (default: strict)
- `--trust-file-order`: Enable file-order/duration-based assignment mode for episode matching. When set, NameGnome will use the order and duration of files to assign episode spans (or singles) when titles are missing. This is robust for anthology and non-anthology shows, and is attempted before manual fallback. (Sprint 3)

### Examples

```sh
# Scan a TV directory with anthology pairing and custom show name
namegnome scan /media/TV/PawPatrol --media-type tv --show-name "Paw Patrol" --anthology

# Scan movies, download artwork, and output JSON
namegnome scan /media/Movies --media-type movie --movie-year 2023 --artwork --json

# Mixed library scan with two media types and no-color (CI-friendly)
namegnome scan /media/Library --platform plex --media-type tv --media-type movie --no-color
```

### Exit Codes

- `0`: Success
- `1`: Error
- `2`: Manual intervention needed (e.g., low-confidence LLM result)

## apply

Apply a saved rename plan, moving files as specified.

### Usage

```sh
namegnome apply <plan-id> [OPTIONS]
```

- `<plan-id>`: ID of the plan to apply (autocompletes from available plans)

### Options

- `--verify`: Verify file hashes after move
- `--skip-identical/--no-skip-identical`: Skip moves if destination exists and
  hash matches (default: skip)
- `--no-progress`: Disable progress bar (for scripting/CI)
- `--json`: Output results as JSON
- `--no-color`: Disable colored output

### Examples

```sh
namegnome apply 123e4567-e89b-12d3-a456-426614174000
namegnome apply latest --verify --no-progress
```

### Exit Codes

- `0`: All files moved successfully
- `1`: Error (e.g., hash mismatch, move failure)
- `2`: Manual intervention needed

## undo

Revert a previously applied rename plan, restoring all files to their original
locations **and cleaning up any empty directories created by apply**.

### Usage

```sh
namegnome undo <plan-id> [OPTIONS]
```

- `<plan-id>`: ID of the plan to undo (autocompletes from available plans)

### Options

- `--yes`: Skip confirmation prompt and undo immediately
- `--no-progress`: Disable progress bar
- `--json`: Output results as JSON
- `--no-color`: Disable colored output
- `--no-rich`: Disable Rich spinners/progress bars (falls back to plain `print`)

> **Note:** After restoring files, undo will automatically remove any empty directories created by apply, restoring your library's directory structure to its pre-apply state. This is always enabled and safe.

### Examples

```sh
namegnome undo 123e4567-e89b-12d3-a456-426614174000
namegnome undo latest --yes --no-progress
```

### Exit Codes

- `0`: Undo completed successfully
- `1`: Error (e.g., source exists, destination missing)

## clean-plans

Delete old rename plans from the NameGnome plan store (`~/.namegnome/plans/` in your home directory).

### Usage

```sh
namegnome clean-plans [OPTIONS]
```

### Options

- `--keep <N>`: Number of most recent plans to keep (default: 0, deletes all)
- `--yes`: Skip confirmation prompt and delete immediately

### Examples

```sh
# Delete all plans:
namegnome clean-plans

# Keep the 5 most recent plans:
namegnome clean-plans --keep 5

# Delete all plans without confirmation:
namegnome clean-plans --yes
```

### Exit Codes

- `0`: Success
- `1`: Error or aborted by user

## plans

List and inspect plan files in `~/.namegnome/plans/` (your home directory).

### Usage

```sh
namegnome plans [PLAN_ID] [OPTIONS]
```

### Options
- `--json`: Output as JSON for scripting/automation
- `--show-paths`: Show full file paths
- `--status`: Show plan status summary (pending, moved, etc.)
- `--latest`: Show the most recent plan

### Examples

```sh
namegnome plans                # List all plans
namegnome plans --status       # Show status summary for each plan
namegnome plans --show-paths   # Show full file paths
namegnome plans <PLAN_ID>      # Show details for a specific plan
namegnome plans --json         # Output as JSON for scripting
namegnome plans --latest       # Show the most recent plan
```

## version

Show the installed NameGnome version.

### Usage

```sh
namegnome version
```

## config

Inspect resolved configuration settings (API keys, cache paths, etc.).

### Usage

```sh
namegnome config --show
```

### Options

- `--show`: Pretty-print all resolved settings.

## llm

Manage available LLM models for fuzzy matching. (Sub-commands)

### list

List models discovered by the local Ollama server.

```sh
namegnome llm list
```

### set-default

Set the default model used when `--llm-model` is omitted.

```sh
namegnome llm set-default llama3:8b
```

## Advanced Usage

- All commands support `--help` for detailed flag descriptions.
- Plan IDs can be autocompleted from available plans in `~/.namegnome/plans/` (home directory).
- Use `--json` and `--no-color` for scripting and CI integration.
- LLM model selection and manual override flags are available for advanced
  renaming scenarios.

## See Also

- [apply-undo.md](apply-undo.md): Transactional guarantees and rollback
- [progress-logging.md](progress-logging.md): CLI output and logging
- [hashing.md](hashing.md): Integrity checks
- [integration-testing.md](integration-testing.md): End-to-end test philosophy
- [README.md](../README.md): CLI usage and quick start

- When episode titles are missing, the planner uses file duration and canonical episode runtimes to assign episode spans (or singles) to files. This duration-based assignment is robust for anthology and non-anthology shows, and is attempted before manual fallback. (Sprint 2) 