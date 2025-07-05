# NameGnome Scan Phase: Rules & Requirements (Source of Truth)

This document defines the **requirements, expected behaviors, and rules** for the Scan phase in NameGnome. It is the authoritative reference for all contributors and AI assistants. Update as needed to reflect evolving standards and edge cases.

---

## 1. General Requirements
- Recursively scan a user-specified directory for media files.
- Identify and classify files as TV, Movie, Music, or Unknown using:
  - File extensions (must match supported media types)
  - Filename patterns (e.g., S01E01, 1x01, etc.)
  - Directory hints (e.g., "TV Shows", "Movies")
- Skip non-media, sidecar, and hidden files (unless configured otherwise).
- Build a list of MediaFile objects with all relevant metadata.
- Return a ScanResult with all found media files, errors, and stats.

---

## 2. Standard Case Behaviors
- **TV Shows:**
  - Extract show name from filename, parent directory, or explicit config.
  - Detect season number, episode number, and episode title from filename (e.g., S01E01, 1x01, etc.).
  - Query TVDB (on failure falling back to TMDB, then OMDb) to get canonical episode numbering and titles by season
    - If a Show Name returns multiple series, prompt the user for clarification (e.g., Danger Mouse => Danger Mouse (1989), Danger Mouse (2015))
  - Parse episode titles (if detected) from input filenames
    - ONLY if no episode titles are detected, fall back to episode numbering.
    - If only numbers are detected, use those for assignment.
  - **NEW (Sprint 2):** If episode titles are missing, the planner uses file duration and canonical episode runtimes to assign episode spans (or singles) to files. This duration-based assignment is robust for anthology and non-anthology shows, and is attempted before manual fallback.
  - Support multi-episode spans in files (e.g., S01E01-E02) in both anthology and non-anthology format shows. (exe: A non-anthology show file may be a span if the database treats a double length episode as two or more separate canonical episodes. Superman The Animated Series has a triple-length first episode, that is normally syndicated into 3 separate episodes per TVDB)
  - **All canonical episode lists from TVDB, TMDB, and OMDb now include a normalized 'runtime' field (int, minutes, or None) for every episode. This is guaranteed for all downstream consumers.**
- **Movies:**
  - Detect movie year from filename (e.g., "Inception (2010)").
  - Extract movie title from filename or parent directory.
- **Music:**
  - Detect track/album/artist from directory structure and filename.
- **Unknown:**
  - Gracefully fail and inform the user they must 
    - indicate a Media Type before proceeding
    - clarify Show Name or Season if these can't be parsed by earlier steps
    - if not marked as an anthology series, and the canonical episode list is roughly double in length (or greater) than the number of target directory files, ask user if this is an anthology series (files contain spanned canonical episodes) before proceeding. (A user may not have all episodes of a season, but that doesn't mean we )

---

## 3. Edge Case Handling
- **Hidden files/directories:**
  - Skip by default; include if `include_hidden` is set.
- **Non-ASCII filenames:**
  - Must be supported and not cause errors.
- **Sidecar/subtitle/artwork files:**
  - Always skipped (e.g., .srt, .nfo, .jpg, .png).
    - TODO: add support for subtitles, following Plex naming conventions 
- **Ambiguous or malformed filenames:**
  - If unable to confidently classify, mark as manual or unknown.
- **Anthology/multi-episode files:**
  - Attempt to parse and split episode titles from input filenames and map to correct cannonical episode titles.
    - We are seeking to conform input to canonical episode numbering and titles!
      - Always assume input filename numbering is wrong if episode titles are detected!
      - A user always wants to conform to the API response so the correct metadata is mapped in the Media Server client (exe: Plex needs TV Shows to match TVDB or they will mismatch metadata)
  - If no titles are detected, it is safe to assume that input episode numbering is correct, and we can pair titles from matching canonical episode numbering
  - There may situations where a user will know that their sequential input numbering is correct, but their attached titles are incorrect (exe: Sonarr will rename files based off TVDB, even though episodes are spans. Users will know numbering is correct, but titles are incorrect)
    - if this is the case we need to
      - check the API response for episode length
      - Assume anthology series are ~20-30 minutes in length
      - Iteratively progress from the first numerical input file and 
        - iteratively pair canonical half-length episodes as spans (exe: INPUT: [EP1, EP2], OUTPUT: [E01-E02, E03-E04])
        - Do not span iteratively discovered double-length episodes (exe: if input EP3 is 22 minutes instead of 11 => E05)
  - If still too ambiguous, mark for manual review.
- **Nonexistent or non-directory paths:**
  - Raise clear errors and do not proceed.

---

## 4. Confidence Thresholds & Exit Code Semantics

### Confidence Thresholds
NameGnome uses confidence scores to determine the appropriate action for each file during the scan process:

- **≥ 0.75**: Auto-processed (high confidence)
  - Files with clear patterns and strong metadata matches
  - Items are automatically included in the plan without manual review
  - Status: `auto`

- **0.40 - 0.74**: Manual review required (medium confidence)
  - Files with ambiguous patterns or weak metadata matches
  - Items are flagged for manual review and highlighted in CLI output
  - Status: `manual`

- **< 0.40**: Unsupported (low confidence)
  - Files with unclear patterns or no metadata matches
  - Items are marked as unsupported and may be skipped
  - Status: `unsupported`

### Exit Code Semantics
The scan command returns specific exit codes to indicate the result and required next actions:

- **0**: Success
  - All files processed successfully with auto or manual status
  - No critical errors encountered
  - Plan JSON created successfully

- **1**: Error
  - Critical errors encountered during scan
  - Provider failures (all providers failed)
  - File system errors or permission issues
  - Invalid command arguments

- **2**: Manual intervention needed
  - Some files require manual review (confidence 0.40-0.74)
  - Plan contains items flagged as manual
  - User intervention required before applying plan

- **3**: Unsupported input
  - Files with unsupported extensions or formats
  - Malformed filenames that cannot be processed
  - Invalid directory structures

### Provider Fallback Chain
When primary providers fail, the system follows this fallback sequence:

1. **TVDB** (primary) - The Movie Database for TV shows
2. **TMDB** (secondary) - The Movie Database for movies and TV
3. **OMDb** (tertiary) - Open Movie Database
4. **AniList** (quaternary) - Anime and manga database

If all providers fail, items are marked for manual review and exit code 2 is returned.

---

## 5. Cross-Platform & Safety Rules
- All paths must be absolute.
- All logic must work on Windows, macOS, and Linux.
- No OS-specific path or file handling.
- Never modify or move files during scan (scan is read-only).

---

## 6. Extensibility & Modularity
- All scan logic must be modular and testable.
- TV/movie/music rules must be easily extendable for new platforms or naming conventions.
- All configuration must be explicit via `ScanOptions`.

---

## 7. Testability & Coverage
- Every function/class must have:
  - 1 expected-flow test
  - 1 edge case test
  - 1 failure case test
- All edge cases and regressions must be covered by tests.
- Coverage threshold: 85% minimum (updated for Sprint 1.6).

---

## 8. Error Handling & Reporting
- All errors (file access, parse failures, etc.) must be logged and included in `ScanResult.errors`.
- No silent failures.
- Manual/ambiguous cases must be clearly flagged for downstream review.

---

## 9. Naming & Metadata Rules
- Follow the MEDIA-SERVER FILE-NAMING & METADATA GUIDE for all pattern matching and classification.
- Use platform presets and naming conventions for all output and classification.

---

## 10. CLI/UX Rules
- All scan options must be available via CLI flags.
- Output must be clear, colorized (unless disabled), and suitable for both human and script consumption (JSON mode).

---

## 11. Documentation & Maintainability
- All scan logic must be documented with module-level and function-level docstrings.
- All rules, edge cases, and platform-specific behaviors must be documented in this file and/or the codebase.

---

## 12. TO-DO
- Absolute numbering leveraging client AniList and AniDB
  - reimplement AniDB client (lost at some point in refactoring)
- Subtitle support for Movies and TV Shows
- Movie logic
- Music logic

*Update this file as requirements evolve. This is the single source of truth for Scan phase rules and expected behavior.*
