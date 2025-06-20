# MVP_CHANGELOG.md

> **Purpose:** Track progress on each sub-step of the MVP SCAN → APPLY → UNDO workflow for TV files. Use checkboxes for each actionable item. Update as tasks are started, in progress, or completed.

---

## 1. CLI `apply` Command (MVP)
- [x] Add `apply` command to Typer CLI (`cli/commands.py` or similar)
- [x] Accept a plan ID or path as argument; load the plan from `.namegnome/plans/`
- [x] For each plan item, call `atomic_move` to move the file from source to destination
- [x] Update each item's status (`MOVED`, `SKIPPED`, `FAILED`) in the plan as moves complete
- [x] On failure, stop and record error; do not proceed with further moves
- [x] Print a summary table of results to the console (Rich table)
- [x] Save the updated plan file with new statuses
- [x] Tests for CLI apply command

_All Step 1 CLI apply command requirements and tests are now complete as of 2025-06-04._

_Last reviewed: 2025-06-04. See MVP_TASK.md for audit details._

## 2. Atomic Move & Overwrite Logic (MVP)
- [x] Implement or reuse `atomic_move(src, dst, *, dry_run=False, overwrite=False)` in `fs/operations.py`
- [x] Handle cross-device moves, Windows path limits, and overwrite logic (skip identical, remove non-identical)
- [x] Add dry-run mode for testing without actual file changes
- [x] Write unit tests for all move scenarios (success, overwrite, dry-run, error)

_All Step 2 atomic move & overwrite requirements and tests are now complete as of 2025-06-04._

## 3. Plan Status Update & Persistence
- [x] After each move in `apply`, update the corresponding plan item's status and reason (if failed/skipped)
- [x] Save the updated plan JSON to disk after all moves (or after each move for robustness)
- [x] Ensure plan can be reloaded with correct statuses for undo
- [x] Add tests for plan status update and persistence

_All Step 3 plan status update & persistence requirements and tests are now complete as of 2025-06-04._

## 4. CLI `undo` Command (MVP)
- [x] Add `undo` command to Typer CLI
- [x] Accept a plan ID or path as argument; load the plan from `.namegnome/plans/`
- [x] For each plan item with status `MOVED`, move the file from destination back to source
- [x] Update each item's status to `UNDONE` (or similar) after successful revert
- [x] Print a summary table of results to the console
- [x] Save the updated plan file with new statuses
- [x] Tests for CLI undo command

_All Step 4 CLI undo command requirements and tests are now complete as of 2025-06-04._

## 5. Rollback/Undo Safety & Error Handling
- [x] Before moving a file back, check if the source already exists; if so, skip and mark as FAILED with reason
- [x] On any error, stop and print a clear error message
- [x] Add tests for partial undo, file exists, and error scenarios

_All Step 5 rollback/undo safety and error handling requirements and tests are now complete as of 2025-06-04._

## 6. End-to-End Demo Test & Docs
- [x] Write an integration test that scans a test directory, applies a plan, and undoes it, asserting file state at each step
- [x] Add CLI usage examples for scan, apply, and undo to the README or a new DEMO.md
- [x] Document known limitations and next steps for post-MVP

_All Step 6 end-to-end demo test & documentation requirements are now complete as of 2025-06-04._

🎉 **MVP is now fully complete!** 🎉

---

*Update this checklist as you make progress on each sub-task. Mark items as [x] when completed.*
