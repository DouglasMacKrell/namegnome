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

---

### 0.4 TV Plan Orchestration: Implement Core Functions

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

* **Goal:** Make prompt construction and response parsing robust to edge cases.
* **Test(s) to Write:**
  - Add tests for malformed/ambiguous LLM responses, prompt size limits, cache hits, and manual fallback.
* **Acceptance Criteria:**
  - No prompt/response errors in edge-case tests; all tests pass.
* **Refactor/Docs:**
  - Refactor prompt templates and response handling for clarity and robustness; document in code and `RECOVERY_PLAN.md`.
* **Done when:**
  - No prompt/response errors in edge-case tests and code is refactored.

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