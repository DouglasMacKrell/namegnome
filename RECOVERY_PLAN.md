# RECOVERY_PLAN.md

> **Purpose:**  
> This document tracks the step-by-step recovery and improvement plan for NameGnome's Scan LLM fuzzy logic, anthology handling, and LLM integration.  
> Each ticket is atomic, actionable, and can be checked off as completed.

---

## Test-Driven Development (TDD) Policy

All work in this recovery plan must follow TDD:
- **Write or update a failing test before fixing/adding code.**
- **Only write the minimum code to make the test pass.**
- **Refactor with tests green.**
- **Document test coverage and rationale for each ticket.**
- **No ticket is complete until all acceptance criteria are met and tests pass.**

---

## 1 · Sprint 0: Recovery & Baseline Restoration

### 0.1 Fix Critical Import/Module Errors

* **Goal:** Restore basic scan/plan CLI functionality.
* **Test(s) to Write:**
  - Add/restore a CLI integration test that runs `scan` and expects a successful plan output (should fail due to import error).
* **Acceptance Criteria:**
  - Test passes with no import errors and correct plan output.
* **Refactor/Docs:**
  - Refactor import logic for maintainability; document in code and `RECOVERY_PLAN.md`.
* **Done when:**
  - CLI scan test passes and code is refactored.

---

### 0.2 LLM Integration Audit & Repair

* **Goal:** Ensure LLM (Ollama) integration is functional and robust.
* **Test(s) to Write:**
  - Add/restore tests for LLM connection, model listing, and prompt execution (mock Ollama if needed).
  - Add CLI test for `--llm-model` flag.
* **Acceptance Criteria:**
  - LLM features work in CLI and all tests pass.
* **Refactor/Docs:**
  - Refactor LLM integration for clarity and error handling; document in code and `RECOVERY_PLAN.md`.
* **Done when:**
  - LLM features work in CLI and tests pass.

---

### 0.3 Fuzzy Matching & Anthology Fallback Review

* **Goal:** Audit and restore robust fuzzy/anthology fallback logic.
* **Test(s) to Write:**
  - Add/restore tests for:
    - Single-episode matching
    - Anthology/double-episode splitting
    - Fuzzy/rare-noun/token overlap fallbacks
    - LLM fallback and manual flagging
* **Acceptance Criteria:**
  - All expected and edge-case tests pass.
* **Refactor/Docs:**
  - Refactor fuzzy/anthology logic for maintainability; document any missing or stubbed logic in code and `RECOVERY_PLAN.md`.
* **Done when:**
  - All expected and edge-case tests pass and code is refactored.

### 0.3.x Incremental Fixes (Atomised)

#### 0.3.1 Episode-list Normalisation
*Goal:* Ensure `namegnome.core.tv.utils.normalize_episode_list` returns a **list of dicts** whose `season` and `episode` fields are *integers* (no zero-padding) and skips invalid rows, matching both planner and TV-helper expectations.
*Tests to Write/Update:*
  * `tests/core/test_planner.py::TestTVPlannerHelpers::test_normalize_episode_list`
  * `tests/core/test_planner.py::test_normalize_episode_list` (planner variant)
*Done when:* both tests pass without regression elsewhere.

#### 0.3.2 Episode-span Parser Edge-cases
*Goal:* Extend `_parse_episode_span_from_filename` to recognise patterns `E03-E04`, `1x01-1x02`, etc.
*Tests:* `test_parse_episode_span_from_filename`
*Done when:* span tests all pass.

#### 0.3.3 Delimiter & Segment-split Detection
*Goal:* Make `_detect_delimiter` & `_split_segments` pick up " and ", " & ", comma, dash.
*Tests:* `test_detect_delimiter`, `_find_candidate_splits` tests.
*Done when:* delimiter helper tests pass.

#### 0.3.4 Conflict-detection Consolidation
*Goal:* Unify `add_plan_item_with_conflict_detection` so `tests/core/test_planner.py::test_detect_conflicts` passes.
*Done when:* conflict test passes and any planned items get `PlanStatus.CONFLICT` appropriately.

#### 0.3.5 BuildContext-aware Helper Functions
*Goal:* Ensure helper stubs in `core/tv/plan_orchestration.py` work with both `TVPlanContext` and `TVRenamePlanBuildContext` objects (fix AttributeError failures).
*Done when:* `test_handle_normal_plan_item`, `_add_plan_item_and_callback`, `_handle_unsupported_media_type` tests pass.

#### 0.3.6 CLI Artwork Flag Exit-code
*Goal:* Diagnose and fix non-zero exit in `tests/cli/test_scan_command.py::test_scan_command_with_artwork_flag` (likely missing Rich stub/context manager).
*Done when:* CLI test passes (exit_code == 0).

---

### 0.4 Anthology/Double-Episode Handling: Canonical Flow & Edge Cases

> **Critical TDD/robustness requirement for all future anthology/plan work.**

#### Canonical Flow
- **Input prioritization:** If input files have episode titles, always match to canonical metadata from the API. If only episode numbers, trust numbering and use canonical titles for output.
- **Anthology mode:** If --anthology is passed, always treat as double-episode/anthology file. Never mix with dash-span or single-episode logic.
- **Output:** Always output filenames as `Show - S01E01-E02 - Title1 & Title2.ext`, using canonical titles and numbers. Join titles with `&` for multi-episode files.
- **If --untrusted-titles and --max-duration are passed:** Ignore input titles, use episode numbers and durations from API, and pair episodes whose durations sum to max duration. If a single episode's duration matches, treat as single-episode file. If two (or more) consecutive episodes' durations sum to max, treat as a span.
- **Edge cases:** If not enough episodes to pair, fallback to single-episode logic. If durations do not match up, warn or flag for manual review.
- **SONARR/untrusted-titles:** If files are from SONARR or similar, and --untrusted-titles is set, ignore input titles and use only episode numbers and canonical data from API. Pair by duration as above.

#### Flag Effects Table
| Flag(s)                | What it Means/Does                                                                                   |
|------------------------|------------------------------------------------------------------------------------------------------|
| --anthology            | Treat as double-episode/anthology file. Use input titles if present, else trust numbering.           |
| --untrusted-titles     | Ignore input titles. Use only episode numbers and canonical data from API.                           |
| --max-duration=XX      | Use this as the max allowed duration for a file. Pair episodes whose durations sum to this value.    |

#### Reference
- See MEDIA-SERVER FILE-NAMING & METADATA GUIDE.md for naming conventions and edge case handling.

### 0.5 TV Plan Orchestration: Implement Core Functions

* **Goal:** Implement missing core functions in `plan_orchestration.py` and related TV modules to unblock plan/anthology tests and restore TV planning pipeline.
* **Functions to Implement:**
  - `fetch_episode_list`
  - `_add_plan_item_and_callback`
  - `_handle_unsupported_media_type`
  - `_anthology_split_segments`
  - Any other stubs required by failing tests in `test_plan_orchestration.py` and related test modules
* **Test(s) to Write:**
  - For each function, write or update a failing test in the relevant test module (e.g., `test_plan_orchestration.py`).
  - Ensure tests cover normal, edge, and error cases for each function.
* **Acceptance Criteria:**
  - All plan orchestration and anthology-related tests pass (or are meaningfully skipped if not yet in scope).
  - Functions are minimally implemented to pass tests, with clear docstrings and TODOs for future enhancement.
* **Refactor/Docs:**
  - Refactor orchestration logic for clarity and maintainability; document any stubbed or incomplete logic in code and `RECOVERY_PLAN.md`.
* **Done when:**
  - All orchestration/anthology tests pass and code is refactored.

---

## 2 · Sprint 1: Robustness & Edge-Case Hardening

### 1.1 LLM Prompt & Response Handling

* **Goal:** Make prompt construction and response parsing robust to edge cases. **✅ Completed**
* **Test(s) to Write:**
  - Add tests for malformed/ambiguous LLM responses, prompt size limits, cache hits, and manual fallback.
* **Acceptance Criteria:**
  - No prompt/response errors in edge-case tests; all tests pass.
* **Refactor/Docs:**
  - Refactor prompt templates and response handling for clarity and robustness; document in code and `RECOVERY_PLAN.md`.
* **Done when:**
  - No prompt/response errors in edge-case tests and code is refactored. **(Met 2025-06-19)**

> **Sprint 1.1 Summary (2025-06-19):**
> * Added robust comment stripping and single-quoted key handling in `sanitize_llm_output` to better parse messy LLM responses (supports `/* … */`, `<!-- … -->`, and `#` comments).
> * Confirmed prompt size checks, cache hits/bypass logic, and manual fallback behaviour via existing test-suite.
> * All LLM prompt & parsing tests now pass, satisfying acceptance criteria.
> * Documentation updated here; further template polishing deferred to Sprint 2 docs ticket.

---

### 1.2 Anthology & Span Matching Improvements

* **Goal:** Ensure all anthology and episode span edge cases are handled.
* **Test(s) to Write:**
  - Add regression tests for known anthology edge cases (Paw Patrol, Martha Speaks, etc.).
  - Add tests for windowed split logic for ambiguous double-episode files.
* **Acceptance Criteria:**
  - All anthology edge-case tests pass.
* **Refactor/Docs:**
  - Refactor anthology logic for maintainability; document logic and rationale in code and `SCAN.md`.
* **Done when:**
  - All anthology edge-case tests pass and code is refactored.

### 1.2.1 Anthology/Double-Episode Handling: Canonical Flow & Edge Cases

* **Goal:** Ensure all anthology and episode span edge cases are handled. **✅ Completed**

#### Canonical Flow
- **Input prioritization:** If input files have episode titles, always match to canonical metadata from the API. If only episode numbers, trust numbering and use canonical titles for output.
- **Anthology mode:** If --anthology is passed, always treat as double-episode/anthology file. Never mix with dash-span or single-episode logic.
- **Output:** Always output filenames as `Show - S01E01-E02 - Title1 & Title2.ext`, using canonical titles and numbers. Join titles with `&` for multi-episode files.
- **If --untrusted-titles and --max-duration are passed:** Ignore input titles, use episode numbers and durations from API, and pair episodes whose durations sum to max duration. If a single episode's duration matches, treat as single-episode file. If two (or more) consecutive episodes' durations sum to max, treat as a span.
- **Edge cases:** If not enough episodes to pair, fallback to single-episode logic. If durations do not match up, warn or flag for manual review.
- **SONARR/untrusted-titles:** If files are from SONARR or similar, and --untrusted-titles is set, ignore input titles and use only episode numbers and canonical data from API. Pair by duration as above.

#### Flag Effects Table
| Flag(s)                | What it Means/Does                                                                                   |
|------------------------|------------------------------------------------------------------------------------------------------|
| --anthology            | Treat as double-episode/anthology file. Use input titles if present, else trust numbering.           |
| --untrusted-titles     | Ignore input titles. Use only episode numbers and canonical data from API.                           |
| --max-duration=XX      | Use this as the max allowed duration for a file. Pair episodes whose durations sum to this value.    |

#### Reference
- See MEDIA-SERVER FILE-NAMING & METADATA GUIDE.md for naming conventions and edge case handling.

* **Done when:**
  - All anthology edge-case tests pass and code is refactored. **(Met 2025-06-19)**

> **Sprint 1.2.1 Summary (2025-06-19):**
> * Implemented canonical span naming (`S01E01-E02` → `01-E02`) and ampersand-joined titles.
> * Added per-file pairing for untrusted-titles with max-duration, leveraging episode durations.
> * All canonical flow hotspot tests now pass (`test_tv_anthology_canonical_flow_hotspot`).
> * Edge-case tests now behave as expected, with only designed XFAIL remaining.

---

### 1.3 Provider Fallback & Episode List Normalization

* **Goal:** Ensure robust fallback between TVDB, TMDB, OMDb for episode lists.
* **Test(s) to Write:**
  - Add tests for provider fallback scenarios and missing data.
  - Add tests for episode list normalization across providers.
* **Acceptance Criteria:**
  - Fallback works and all tests pass.
* **Refactor/Docs:**
  - Refactor provider logic for clarity and normalization; document in code and `RECOVERY_PLAN.md`.
* **Done when:**
  - Fallback works, all tests pass, and code is refactored.

---

## 3 · Sprint 2: Test Coverage & Documentation

### 2.1 Test Migration & Coverage Lift

* **Goal:** Migrate legacy tests and ensure 80%+ coverage for scan/LLM logic.
* **Test(s) to Write:**
  - Move/expand tests to match new module structure.
  - Add missing edge/failure case tests.
  - Run coverage and document any remaining gaps.
* **Acceptance Criteria:**
  - Coverage threshold met and all tests green.
* **Refactor/Docs:**
  - Refactor tests for maintainability; document coverage in `RECOVERY_PLAN.md`.
* **Done when:**
  - Coverage threshold met and all tests green.

---

### 2.2 Documentation & Developer Onboarding

* **Goal:** Ensure all scan/LLM logic is documented and easy to onboard.
* **Test(s) to Write:**
  - N/A (documentation ticket)
* **Acceptance Criteria:**
  - Docs are up to date and reviewed.
* **Refactor/Docs:**
  - Update `SCAN.md`, `SCAN_RULES.md`, and `README.md` with current logic and examples.
  - Add developer notes for LLM integration, prompt editing, and test writing.
* **Done when:**
  - Docs are up to date and reviewed.

---

## 4 · Sprint 3: Feature Enhancements (Optional)

- Absolute numbering (AniList/AniDB)
- Subtitle support
- Movie/music scan logic parity

---

**How to use:**  
- Add, update, or check off tickets as you progress.
- Reference this plan in PRs and daily standups.
- Keep each ticket atomic and actionable. 