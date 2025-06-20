# MVP_TASK.md

> **Goal:** Achieve a working end-to-end demo of the core NameGnome workflow for TV files: SCAN => APPLY => UNDO. This file tracks the minimum atomized tasks required to reach MVP status for a live demo, focusing on actionable, testable steps. Use this as the single source of truth for MVP progress.

---

## MVP Workflow: TV SCAN → APPLY → UNDO

### 1. CLI `apply` Command (MVP)
* **Goal:** Implement a CLI command to apply a rename plan, moving files as specified and updating plan status.
* **Steps:**
  1. Add `apply` command to Typer CLI (`cli/commands.py` or similar).
  2. Accept a plan ID or path as argument; load the plan from `.namegnome/plans/`.
  3. For each plan item, call `atomic_move` to move the file from source to destination.
  4. Update each item's status (`MOVED`, `SKIPPED`, `FAILED`) in the plan as moves complete.
  5. On failure, stop and record error; do not proceed with further moves.
  6. Print a summary table of results to the console (Rich table).
  7. Save the updated plan file with new statuses.
* **Done when:** CLI `apply` command moves files per plan, updates statuses, and prints a summary. All code is tested and E501-compliant.

### 2. Atomic Move & Overwrite Logic (MVP)
* **Goal:** Ensure all file moves are atomic, cross-platform, and safe, with overwrite and dry-run support.
* **Steps:**
  1. Implement or reuse `atomic_move(src, dst, *, dry_run=False, overwrite=False)` in `fs/operations.py`.
  2. Handle cross-device moves, Windows path limits, and overwrite logic (skip identical, remove non-identical).
  3. Add dry-run mode for testing without actual file changes.
  4. Write unit tests for all move scenarios (success, overwrite, dry-run, error).
* **Done when:** All move scenarios are covered by tests and used by the `apply` engine.

### 3. Plan Status Update & Persistence
* **Goal:** Persist plan item status after each move, enabling accurate undo and audit.
* **Steps:**
  1. After each move in `apply`, update the corresponding plan item's status and reason (if failed/skipped).
  2. Save the updated plan JSON to disk after all moves (or after each move for robustness).
  3. Ensure plan can be reloaded with correct statuses for undo.
  4. Add tests for plan status update and persistence.
* **Done when:** Plan file reflects up-to-date statuses after apply; reload and undo work as expected.

### 4. CLI `undo` Command (MVP)
* **Goal:** Implement a CLI command to revert a previously applied plan, restoring all files to their original locations.
* **Steps:**
  1. Add `undo` command to Typer CLI.
  2. Accept a plan ID or path as argument; load the plan from `.namegnome/plans/`.
  3. For each plan item with status `MOVED`, move the file from destination back to source.
  4. Update each item's status to `UNDONE` (or similar) after successful revert.
  5. Print a summary table of results to the console.
  6. Save the updated plan file with new statuses.
* **Done when:** CLI `undo` command restores all files, updates statuses, and prints a summary. All code is tested and E501-compliant.

### 5. Rollback/Undo Safety & Error Handling
* **Goal:** Ensure undo is robust to partial failures and does not overwrite existing files without warning.
* **Steps:**
  1. Before moving a file back, check if the source already exists; if so, skip and mark as `FAILED` with reason.
  2. On any error, stop and print a clear error message.
  3. Add tests for partial undo, file exists, and error scenarios.
* **Done when:** Undo is robust, safe, and all error cases are covered by tests.

### 6. End-to-End Demo Test & Docs
* **Goal:** Validate the full SCAN → APPLY → UNDO workflow and document usage for demo.
* **Steps:**
  1. Write an integration test that scans a test directory, applies a plan, and undoes it, asserting file state at each step.
  2. Add CLI usage examples for scan, apply, and undo to the README or a new DEMO.md.
  3. Document known limitations and next steps for post-MVP.
* **Done when:** End-to-end test passes and demo instructions are clear.

---

*Update this file as tasks are completed or new issues are discovered during MVP implementation.* 