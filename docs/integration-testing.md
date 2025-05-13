# Integration Testing: End-to-End Reliability in NameGnome

This document describes the philosophy, structure, and guarantees of
integration testing in NameGnome. Integration tests ensure that all core
workflows—scan, apply, undo, and error handling—work reliably across
platforms and real-world scenarios.

## Philosophy

- **Realism:** Tests mimic actual user workflows, including CLI commands,
  filesystem operations, and error conditions.
- **Safety:** Integration tests catch regressions and edge cases before they
  reach users.
- **Coverage:** All critical paths (success, failure, rollback, skip-identical)
  are tested end-to-end.
- **Cross-platform:** Tests run on Windows, macOS, and Linux in CI.

## Structure

- Integration tests live in `tests/cli/` and `tests/core/` (mirroring source
  structure).
- Tests use `pytest` for orchestration and fixtures.
- CLI commands are invoked via `subprocess.run` or Typer's test runner.
- Temporary directories (`tmp_path`, `tmp_path_factory`) isolate test data.

## Test Types

- **CLI End-to-End:** Simulate user commands (`scan`, `apply`, `undo`) and
  assert on output, exit codes, and filesystem state.
- **Error Cases:** Test hash mismatches, partial moves, and rollback triggers.
- **Cross-Platform:** Platform-specific tests skip when not on the target OS.
- **Log & Output Validation:** Capture and assert on Rich output, log files,
  and summary tables.

### Example: CLI Test (Pytest)

```python
def test_apply_and_undo(tmp_path):
    # Arrange: create source files and plan
    # ...
    # Act: run 'namegnome apply' and 'namegnome undo' via subprocess
    # ...
    # Assert: files are moved/restored, output is correct
```

### Example: Error Case

```python
def test_hash_mismatch_triggers_rollback(tmp_path):
    # Arrange: patch atomic_move to corrupt file after move
    # ...
    # Act: run apply_plan with verify_hash=True
    # ...
    # Assert: plan is rolled back, item marked as FAILED
```

## CI Integration

- All integration tests run in GitHub Actions on Ubuntu, macOS, and Windows.
- Coverage threshold (80%+) is enforced in CI (`pytest --cov-fail-under=80`).
- No skipped or flaky tests are allowed in main/develop branches.

## Guarantees

- **No partial moves:** Tests confirm that after any failure, all files are
  restored to their original state.
- **Auditability:** Log files and plan artifacts are checked for correctness.
- **User-facing output:** All CLI output is validated for clarity and
  correctness.

## Design Rationale

- Integration tests are prioritized for all new features and bugfixes.
- Tests are E501-wrapped and follow Google-style docstring/comment standards.
- Platform-specific logic is always tested on the relevant OS.

## See Also

- [apply-undo.md](apply-undo.md): Transactional guarantees and rollback
- [progress-logging.md](progress-logging.md): CLI output and logging
- [hashing.md](hashing.md): Integrity checks in tests
- [README.md](../README.md): CLI usage and quick start 