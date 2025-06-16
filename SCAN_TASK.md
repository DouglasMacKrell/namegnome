# SCAN_TASK.md

## Roadmap: Multi-Provider Episode Support & CLI Enhancements

This checklist tracks the implementation of robust, normalized episode-level support for TVDB, TMDB, and OMDB in NameGnome, including CLI provider selection, fallback logic, and anthology/episode matching. Each step is atomized for clear, incremental progress.

---

## Legacy Tickets (Quarantined)

> **Note:** The following tickets are preserved for historical reference and may contain approaches or requirements that are now superseded by current plans. Only revisit these if a gap is discovered in the new roadmap, or for context on past decisions. Do not implement any legacy ticket that contradicts the current canonical data policy, scan flow, or modularization standards.

# BEGIN LEGACY TICKETS

## 2025-05-29: Modular Refactor Plan for TV Scan Logic

- **Context:**
  - `src/namegnome/core/tv_planner.py` has grown to 2,293 lines, violating the project rule that no file should exceed 500 lines.
  - TV scan/plan logic is currently monolithic; modularity and maintainability are at risk.
- **Goal:**
  - Split TV scan logic into feature-focused modules/packages without breaking functionality or being destructive.
  - Ensure all changes are incremental, reviewable, and preserve test coverage.
- **Proposed Modular Structure:**
  - `tv_planner.py`: Main orchestration/entry points only.
  - `anthology.py`: Anthology-specific logic (splitting, matching).
  - `episode_parser.py`: Filename/season/episode extraction.
  - `plan_conflicts.py`: Plan item creation, conflict detection.
  - `plan_context.py`: Context/data classes for planning.
  - `utils.py`: Shared helpers (sanitization, normalization).
- **Incremental Refactor Steps:**
  1. Move utility/helper functions (e.g., `sanitize_title`, normalization, regex helpers) to `utils.py`.
  2. Move context/data classes to `plan_context.py`.
  3. Move anthology-specific logic to `anthology.py`.
  4. Move episode/season extraction to `episode_parser.py`.
  5. Move plan item/conflict logic to `plan_conflicts.py`.
  6. Update imports in `tv_planner.py` to use the new modules.
  7. Ensure all tests pass after each step.
- **Notes:**
  - Each move should be accompanied by module-level docstrings and E501-compliant wrapping.
  - No changes to function signatures or logic during the move.
  - Proceed in small, reviewable increments.
- **Next Action:**
  - Begin with utility/helper function extraction, or as prioritized by the team.
- [x] Created `core/tv/` subpackage and `__init__.py` for TV logic isolation.
- [ ] Incrementally move TV logic modules (planner, anthology, parsing, etc.) into `core/tv/`.

### 1. CLI & Config
- [x] Add `--provider [provider name]` flag to the `scan` command (default: tvdb).
- [x] Update CLI help and docs to describe the new flag and provider options.

### 2. TMDB: Episode-Level Support
- [x] Implement TMDB API call to fetch series details and enumerate seasons.
- [x] Implement TMDB API call to fetch all episodes for a given season.
- [x] Write a function to aggregate all episodes across all seasons.
- [x] Map TMDB episode data to the `TVEpisode` model.
- [x] Integrate episode list into the `MediaMetadata` model.
- [x] Handle TMDB API errors (network, missing data, rate limits).
- [x] Write unit tests for each function (fetch series, fetch season, map episode).
- [x] Write integration test for full TMDB episode list fetch.

### 3. OMDB: Episode-Level Support
- [x] Implement OMDB API call to fetch series details and enumerate seasons (by IMDb ID).
- [x] Implement OMDB API call to fetch all episodes for a given season.
- [x] Write a function to aggregate all episodes across all seasons.
- [x] Map OMDB episode data to the `TVEpisode` model.
- [x] Integrate episode list into the `MediaMetadata` model.
- [x] Handle OMDB API errors (rate limits, missing data, partial results).
- [x] Write unit tests for each function (fetch series, fetch season, map episode).
- [x] Write integration test for full OMDB episode list fetch.

### 4. Planner/Scan Logic
- [ ] Refactor planner to accept episode lists from any provider.
- [x] Add provider-agnostic logic for anthology splitting and episode matching.
- [x] Add provider-specific fallbacks if episode data is incomplete.
- [ ] Write tests for planner with TVDB, TMDB, and OMDB episode data.

### 5. Fallback & User Prompts
- [ ] Implement prompt for provider-specific ID entry (TVDB, TMDB, OMDB).
- [ ] Implement prompt to switch provider if episode data is missing.
- [ ] Implement prompt to accept manual review for unmatched files.
- [ ] Write tests for each user prompt and fallback scenario.
- [x] Add clear error and info messages for all fallback scenarios.

### 6. Documentation
- [ ] Update `SCAN.md` and CLI docs to reflect new provider support, fallback logic, and limitations.
- [ ] Document known edge cases and troubleshooting steps.

### 7. Testing & Validation
- [ ] Add/extend unit tests for each new API integration function.
- [ ] Add/extend integration tests for CLI with each provider.
- [ ] Add regression tests for anthology and episode-matching logic.
- [ ] Validate error handling and fallback logic with simulated API failures.

### 8. TV Scan Logic Isolation & Documentation (Current Sprint)
- [x] Remove all "Pups" or Paw Patrol-specific hardcoding from fallback logic.
- [x] TV scan logic is now fully isolated in `tv_planner.py`. All TV file handling is delegated to this module from `planner.py`. Movie and Music logic will be isolated in future sprints. See SCAN.md for details.
- [x] Thoroughly document every function, edge case, and design decision in the current TV scan logic.
- [x] Isolate TV scan logic from Movie and Music logic, even if it means code duplication.
    - [x] Identify all code paths shared between TV, Movie, and Music logic.
    - [x] Refactor TV-specific logic into `core/tv_planner.py` (or similar).
    - [x] Ensure Movie and Music logic are not affected by TV changes.
    - [x] Add or update tests to cover the new module boundaries.
    - [x] Mark this item as complete when TV, Movie, and Music logic are isolated and all tests pass.
- [x] Add regression tests for anthology and non-anthology TV shows.
- [x] Document known edge cases, fallback flows, and troubleshooting steps in `SCAN.md`.
- [x] Mark this version as a "golden state" for TV scan logic.
- [x] Sanitize output filenames to remove or replace special characters (e.g., "!", "?", ":", etc.) for portability.

### 9. Music Scan Support (Isolated Sprint)
- [ ] Implement `MusicRuleSet` in `src/namegnome/rules/` for music file renaming (artist/album/track logic).
- [ ] Integrate music metadata extraction (ID3 tags, MusicBrainz, Discogs, etc.).
- [ ] Normalize music metadata fields (artist, album, track, year, etc.).
- [ ] Refactor planner to handle music files and generate rename plan items.
- [ ] Add CLI options for music-specific provider selection and config.
- [ ] Add user prompts for ambiguous or missing music metadata.
- [ ] Add error handling and fallback logic for music scans.
- [ ] Write unit tests for music metadata extraction and mapping.
- [ ] Write integration tests for music scan and plan generation.
- [ ] Document music scan flow, known edge cases, and troubleshooting steps in `SCAN.md`.

### 10. Movie Scan Support (Isolated Sprint)
- [ ] Implement/refine `MovieRuleSet` in `src/namegnome/rules/` for movie file renaming (title/year logic).
- [ ] Integrate movie metadata extraction (TMDB, OMDB, local tags, etc.).
- [ ] Normalize movie metadata fields (title, year, provider IDs, etc.).
- [ ] Refactor planner to handle movie files and generate rename plan items.
- [ ] Add CLI options for movie-specific provider selection and config.
- [ ] Add user prompts for ambiguous or missing movie metadata.
- [ ] Add error handling and fallback logic for movie scans.
- [ ] Write unit tests for movie metadata extraction and mapping.
- [ ] Write integration tests for movie scan and plan generation.
- [ ] Document movie scan flow, known edge cases, and troubleshooting steps in `SCAN.md`.

### 11. LLM Integration Rework
- [ ] Investigate LLM prompt size issues (avoid feeding the entire episode list in every prompt).
- [ ] Explore RAG (Retrieval-Augmented Generation) or persistent LLM context/memory for episode lists.
- [ ] Re-enable and test LLM-based anthology/episode matching only after TV, Movie, and Music logic are stable.
- [ ] Write robust tests for LLM integration, including prompt size, fallback, and error handling.
- [ ] Document LLM integration, limitations, and troubleshooting in `SCAN.md`.

---

# END LEGACY TICKETS

## Current Roadmap, Gap Analysis, and Sprints (Authoritative)

### Gap Analysis: Current vs. Desired Scan Flow

### A. What's Working (Current State)
- Recursively scans directories, classifies files by extension/patterns.
- Skips sidecars/hidden files by default.
- Builds MediaFile and ScanResult objects.
- Handles TV, Movie, Music, and Unknown types.
- Has modular structure and some test coverage.
- Anthology logic attempts to split multi-episode files and uses fuzzy/token matching.

### B. What's Missing or Needs Improvement (per SCAN_RULES.md)
- **Canonical Episode List:**
  - Not all providers (TVDB, TMDB, OMDb) are normalized to include duration.
  - Not all downstream logic expects or uses duration for assignment.
- **Multi-Episode Spans:**
  - Current logic may not reliably map files to multi-episode spans, especially for non-anthology shows with double/triple-length episodes.
  - No robust file-duration-to-episode-span assignment when titles are missing.
- **Provider Fallbacks & User Prompts:**
  - Not all flows prompt the user for ambiguous show names, missing metadata, or anthology detection.
- **Edge Case Handling:**
  - Subtitle/sidecar support is not yet implemented.
  - Non-ASCII, ambiguous, or malformed filenames may not always be handled gracefully.
- **CLI/UX:**
  - No --trust-file-order flag or mode for file-order/duration-based assignment.
  - CLI help/docs may not reflect new/desired behaviors.
- **Testing & Documentation:**
  - Not all new flows (duration, file-order, edge cases) are covered by tests or docs.

---

## Current Plan: Sprints & Atomized Tickets (6/13/2025)

### Sprint 1: Canonical Episode List & Duration Support
- [x] Update all episode list construction logic (TVDB, TMDB, OMDb, etc.) to include a duration field for each episode.
- [x] Normalize and sanitize the duration field for all providers.
- [x] Update all downstream consumers to expect and use the duration field.
- [x] Add/extend tests to ensure duration is present and correct for all supported providers.
- [x] Document the new Episode List structure and duration logic in SCAN.md and code docstrings.

### Sprint 2: File-Order & Duration-Based Assignment
- [x] Implement logic to use file duration and canonical episode durations to assign episode spans (or singles) to filenames when titles are missing.
- [x] Add/extend tests for anthology and non-anthology shows with multi-episode files and no titles.
- [x] Document the file-order/duration assignment logic and edge cases in SCAN.md and CLI help.

### Sprint 3: CLI/UX Enhancements
- [x] Add a CLI/config flag (e.g., --trust-file-order) to enable file-order/duration-based assignment mode.
- [x] Update CLI help and docs to describe the new flag and its behavior.
- [x] Add user prompts and error messages for mismatched file/episode counts, mixed runtimes, or ambiguous assignments.
- [x] Add regression tests for the new mode and all user-facing flows.

### Sprint 4: Edge Case & Provider Handling
- [x] Implement user prompts for ambiguous show names, missing metadata, or anthology detection.  
      _All prompt flows (ambiguous show, missing metadata, anthology detection) are implemented, tested, and documented. See SCAN.md and CLI docs for details._
- [ ] Add support for subtitle/sidecar files (following Plex naming conventions).
- [ ] Ensure robust handling of non-ASCII, ambiguous, or malformed filenames.
- [x] Add/extend tests for all new edge cases.  
      _All prompt and edge case flows now have robust test coverage. See test_plan_orchestration.py._

### Sprint 5: Refactor, Modularize, and Document
- [ ] Refactor planner/scan logic to cleanly separate file-order/duration assignment from title/number-based matching.
- [ ] Ensure all new logic is modular, testable, and documented.
- [ ] Update SCAN.md, CURRENT_SCAN.md, and CLI docs with new flow diagrams and edge case handling for duration-based assignment.

### Sprint 6. Episode Number Normalization
- [ ] Refactor all episode number handling to use zero-padded strings (e.g., "01" not 1).
- [ ] Update tests and CLI output to expect string episode numbers everywhere.

### Sprint 7. Span Assignment Logic
- [ ] Audit and refactor span assignment for multi-episode files (double, triple, irregular-length).
- [ ] Add/extend tests for all multi-episode and edge-case scenarios.

### Sprint 8. Title Matching Robustness
- [ ] Improve fuzzy/adjacency/keyword logic for title-to-canonical matching.
- [ ] Add regression tests for known edge cases and anthology scenarios.

### Sprint 9. Manual Fallback Reliability
- [ ] Ensure ambiguous or unmatchable files are reliably flagged as manual.
- [ ] Add user prompts and CLI output for manual review cases.

### Sprint 10. Canonical API Data Integration (with caveat)
- [ ] Audit and fix canonical episode list usage in all scan/plan flows.
- [ ] Add/extend tests for API edge cases and mismatches (e.g., Firebuds S2 all episodes misattributed in TVDB).
- [ ] **Note:** Canonical episode data should be treated as the single source of truth, regardless of provider (TVDB, TMDB, OMDb). Only fall back to alternate sources or manual assignment if the canonical data is missing, misattributed, or clearly incorrect. Do not "ask mom when dad says no"—prefer explicit user intervention or documentation of the data issue over silent fallback.

### Sprint 11: Planner/Scan Logic Provider-Agnostic Refactor
- [ ] Refactor planner to accept episode lists from any provider (TVDB, TMDB, OMDB, etc.).
- [ ] Write tests for planner with TVDB, TMDB, and OMDB episode data.

### Sprint 12: Documentation & Edge Case Docs
- [ ] Update SCAN.md and CLI docs to reflect new provider support, fallback logic, and limitations.
- [ ] Document known edge cases and troubleshooting steps.

### Sprint 13: Testing & Validation Lift
- [ ] Add/extend unit tests for each new API integration function.
- [ ] Add/extend integration tests for CLI with each provider.
- [ ] Add regression tests for anthology and episode-matching logic.
- [ ] Validate error handling and fallback logic with simulated API failures.

### Sprint 14: Music Scan Support
- [ ] Implement `MusicRuleSet` in `src/namegnome/rules/` for music file renaming (artist/album/track logic).
- [ ] Integrate music metadata extraction (ID3 tags, MusicBrainz, Discogs, etc.).
- [ ] Normalize music metadata fields (artist, album, track, year, etc.).
- [ ] Refactor planner to handle music files and generate rename plan items.
- [ ] Add CLI options for music-specific provider selection and config.
- [ ] Add user prompts for ambiguous or missing music metadata.
- [ ] Add error handling and fallback logic for music scans.
- [ ] Write unit tests for music metadata extraction and mapping.
- [ ] Write integration tests for music scan and plan generation.
- [ ] Document music scan flow, known edge cases, and troubleshooting steps in SCAN.md.

### Sprint 15: Movie Scan Support
- [ ] Implement/refine `MovieRuleSet` in `src/namegnome/rules/` for movie file renaming (title/year logic).
- [ ] Integrate movie metadata extraction (TMDB, OMDB, local tags, etc.).
- [ ] Normalize movie metadata fields (title, year, provider IDs, etc.).
- [ ] Refactor planner to handle movie files and generate rename plan items.
- [ ] Add CLI options for movie-specific provider selection and config.
- [ ] Add user prompts for ambiguous or missing movie metadata.
- [ ] Add error handling and fallback logic for movie scans.
- [ ] Write unit tests for movie metadata extraction and mapping.
- [ ] Write integration tests for movie scan and plan generation.
- [ ] Document movie scan flow, known edge cases, and troubleshooting steps in SCAN.md.

### Sprint 16: LLM Integration Rework (Deferred)
- [ ] Investigate LLM prompt size issues (avoid feeding the entire episode list in every prompt).
- [ ] Explore RAG (Retrieval-Augmented Generation) or persistent LLM context/memory for episode lists.
- [ ] Re-enable and test LLM-based anthology/episode matching only after TV, Movie, and Music logic are stable.
- [ ] Write robust tests for LLM integration, including prompt size, fallback, and error handling.
- [ ] Document LLM integration, limitations, and troubleshooting in SCAN.md.

### Sprint 17: Pre-Commit & CI Merge Readiness
- [ ] Run `black` on all changed files to ensure code formatting compliance.
- [ ] Run `ruff` and fix all lint errors and warnings. If any files are auto-fixed, stage and commit them with `style: ruff auto-fix` before making further manual changes.
- [ ] Run `mypy --strict` to ensure all type checks pass. Fix any type errors.
- [ ] Run `pytest --cov` and ensure all tests pass and coverage is at least 80%.
- [ ] Manually review all docstrings, comments, and documentation for E501 compliance (88 characters or less per line). Auto-formatters are not sufficient for non-code lines.
- [ ] Stage and commit all changes after auto-fixes, pulls, merges, or conflict resolution.
- [ ] Ensure all commit messages follow the project convention (e.g., `NGN-XYZ: concise action description`).
- [ ] Follow the feature → develop → main merge order as described in project rules. Never merge from develop into a feature branch as the final step.
- [ ] Push after every merge and confirm CI passes for the new commit on develop/main.
- [ ] Never attempt to merge, pull, or switch branches with unstaged or uncommitted changes. Always check `git status` and commit after auto-fixes, pulls, or merges.
- [ ] If any pre-commit or CI checks fail, address the issues and repeat the process until all checks pass.

---

*Check off each item as you implement to ensure a complete, robust, and user-friendly scan experience for all supported episode list providers and file assignment modes.*
