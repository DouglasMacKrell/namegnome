![NameGnome](public/images/NameGnome_README_Headder.png)

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

```bash
pip install namegnome
```

## Usage

### Basic Scan

```bash
namegnome scan /path/to/media/files
```

### Platform Selection

```bash
namegnome scan /path/to/media/files --platform plex
namegnome scan /path/to/media/files --platform jellyfin
```

### Media Type Filtering

```bash
# Scan only TV shows
namegnome scan /path/to/media/files --media-type tv

# Scan only movies
namegnome scan /path/to/media/files --media-type movie

# Scan multiple types
namegnome scan /path/to/media/files --media-type tv --media-type movie
```

### TV Show Specific Options

#### Explicit Show Name

```bash
namegnome scan /path/to/media/files --show-name "Paw Patrol"
```

#### Multi-Segment Episode Handling

```bash
# For shows with multiple segments per file (e.g., Paw Patrol)
namegnome scan /path/to/media/files --anthology
```

#### Episode Number Adjustment

```bash
# Adjust episode numbering when files are incorrectly numbered but in correct order
namegnome scan /path/to/media/files --adjust-episodes
```

### Movie Specific Options

#### Explicit Year

```bash
namegnome scan /path/to/media/files --movie-year 2023
```

### Output Options

#### JSON Output

```bash
namegnome scan /path/to/media/files --json
```

#### Disable Colored Output

```bash
namegnome scan /path/to/media/files --no-color
```

### File Verification

```bash
namegnome scan /path/to/media/files --verify
```

### LLM Model Selection

```bash
namegnome scan /path/to/media/files --llm-model "gpt-4"
```

## Examples

### Organizing a TV Show with Multi-Segment Episodes

```bash
namegnome scan /path/to/paw-patrol \
  --show-name "Paw Patrol" \
  --anthology \
  --adjust-episodes
```

### Organizing Movies with Explicit Year

```bash
namegnome scan /path/to/movies \
  --media-type movie \
  --movie-year 2023
```

### Complex Organization

```bash
namegnome scan /path/to/media \
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

- `0`: Success (no files to process or all files processed successfully)
- `1`: Error (general error)
- `2`: Manual intervention needed (conflicts detected or manual review required)

## Notes

- All rename operations require manual review by default
- The tool will detect and report conflicts in target paths
- File integrity verification is optional but recommended
- JSON output is useful for programmatic processing
- The `--anthology` flag is specifically for shows with multiple segments per file
- The `--adjust-episodes` flag helps correct episode numbering when files are in the right order but numbered incorrectly 