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
  specified multiple times.
- `--show-name <name>`: Override detected show name (TV only)
- `--movie-year <year>`: Specify release year for movie files
- `--anthology`: Handle multi-segment episodes (e.g., Paw Patrol)
- `--adjust-episodes`: Fix episode numbering if files are in correct order but
  misnumbered
- `--verify`: Compute and store SHA-256 checksums for file integrity
- `--json`: Output results as JSON
- `--no-color`: Disable colored output (for logs/CI)
- `--llm-model <model>`: Use a specific LLM for fuzzy matching
- `--strict-directory-structure/--no-strict-directory-structure`: Enforce or
  relax platform directory structure (default: strict)

### Examples

```sh
namegnome scan /media/TV/PawPatrol --show-name "Paw Patrol" --anthology
namegnome scan /media/Movies --media-type movie --movie-year 2023
namegnome scan /media/Library --platform plex --media-type tv --media-type movie --json
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
locations.

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

### Examples

```sh
namegnome undo 123e4567-e89b-12d3-a456-426614174000
namegnome undo latest --yes --no-progress
```

### Exit Codes

- `0`: Undo completed successfully
- `1`: Error (e.g., source exists, destination missing)

## Advanced Usage

- All commands support `--help` for detailed flag descriptions.
- Plan IDs can be autocompleted from available plans in `.namegnome/plans/`.
- Use `--json` and `--no-color` for scripting and CI integration.
- LLM model selection and manual override flags are available for advanced
  renaming scenarios.

## See Also

- [apply-undo.md](apply-undo.md): Transactional guarantees and rollback
- [progress-logging.md](progress-logging.md): CLI output and logging
- [hashing.md](hashing.md): Integrity checks
- [integration-testing.md](integration-testing.md): End-to-end test philosophy
- [README.md](../README.md): CLI usage and quick start 