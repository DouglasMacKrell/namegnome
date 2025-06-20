# Apply & Undo Engines: Transactional Renaming and Rollback

This document provides a deep dive into the design, guarantees, and usage of
NameGnome's Apply and Undo engines. These components ensure that all file
renaming operations are safe, auditable, and fully reversible, making
NameGnome suitable for even the most demanding media library workflows.

## Overview

The Apply and Undo engines work together to:
- Execute planned file renames atomically and transactionally
- Verify file integrity using SHA-256 hashes
- Roll back all changes on failure, leaving no partial moves
- Provide clear CLI feedback, progress bars, and error reporting

## Transactional Guarantees

- **All-or-nothing:** If any file move fails (including hash mismatch), all
  previous moves in the plan are rolled back to their original locations.
- **Atomicity:** Each move uses `atomic_move` for cross-platform, safe
  renaming (see [fs-operations.md](fs-operations.md)).
- **Auditability:** Every operation is logged, and plan files are stored for
  future undo.

## Apply Engine

The Apply engine executes a `RenamePlan` (see `models/plan.py`):

1. Iterates over each `RenamePlanItem` in the plan.
2. For each item:
   - If `skip_identical` is enabled and the destination file exists with an
     identical hash, the move is skipped and status is set to `SKIPPED`.
   - Otherwise, calls `atomic_move` to move the file.
   - If `verify_hash` is enabled, computes the SHA-256 hash of the destination
     and compares it to the source hash. If they differ, marks the item as
     `FAILED` and triggers rollback.
   - On success, marks the item as `MOVED`.
3. If any move fails, all previous moves are rolled back in reverse order.
4. Returns an `ApplyResult` dataclass with counts of moved, skipped, and
   failed items, plus a list of failures and total duration.

### Example: CLI Usage

```sh
namegnome apply <plan-id>
```

- Applies the plan with the given ID (autocompletes from available plans).
- Shows a progress bar and logs each move.
- On error, prints a clear message and rolls back all changes.

### Example: Python Usage

```python
from namegnome.core.apply import apply_plan
result = apply_plan(plan, verify_hash=True, skip_identical=True)
if result.success:
    print("All files moved successfully!")
else:
    print(f"Failed items: {result.failures}")
```

## Undo Engine

The Undo engine restores all files in a plan to their original locations **and, as of June 2025, also removes any empty directories created by apply**:

1. Loads the plan file and reverses the source/destination for each item.
2. Prompts for confirmation (unless `--yes` is passed).
3. Iterates over each item, calling `atomic_move` to restore the file.
4. **After all files are restored, recursively removes any empty destination directories created by apply, up to the plan root.**
5. Logs each operation and shows a progress spinner.
6. Handles errors (e.g., source already exists, destination missing) with clear messages and does not overwrite existing files.

**This cleanup is always enabled by default, is safe, and never removes non-empty directories or the plan root.**

### Example: CLI Usage

```sh
namegnome undo <plan-id> [--yes]
```

- Restores all files in the plan.
- Prompts for confirmation unless `--yes` is passed.
- Logs each restore operation and shows progress.

## Error Handling & Edge Cases

- **Hash mismatch:** If the destination file's hash does not match the source
  after move, the item is marked as `FAILED` and rollback is triggered.
- **Source exists on undo:** Undo will not overwrite existing files; prints an
  error and skips the item.
- **Destination missing on undo:** If the file to restore is missing, prints an
  error and skips the item.
- **Partial moves:** The transactional design ensures no partial moves remain
  after any failure.

## Integration with atomic_move and Hashing

- All file moves use `atomic_move` for cross-platform safety (see
  [fs-operations.md](fs-operations.md)).
- Hash verification uses the `sha256sum` utility (see `utils/hash.py`).
- Undo and Apply engines are fully tested for all scenarios (see
  [integration-testing.md](integration-testing.md)).

## Testing & Guarantees

- 100% test coverage for apply/undo logic, including all error and rollback
  scenarios.
- CLI and Python APIs are both tested in unit and integration tests.
- All logic is E501-compliant and follows Google-style docstring/comment
  standards.

## See Also

- [fs-operations.md](fs-operations.md): Atomic file moves
- [integration-testing.md](integration-testing.md): End-to-end test philosophy
- [README.md](../README.md): CLI usage and quick start 